# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Nitrate test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
Persistent cache, multicall support

In order to save calls to server and time, caching support has been
implemented. Every class that handles objects has its own cache and it
is used to save already initialized (fetched) objects from server. Thus
synchronizing the modified data with the server has to be explicitly
requested by the update() method when caching functionality is enabled:

    object.update()

Methods that manipulate caching levels:

    get_cache_level()
    set_cache_level()

Currently, there are four types (levels) of caching:

    CACHE_NONE ......... no caching at all, changes applied immediately
    CACHE_CHANGES ...... cache only local updates of instance attributes
    CACHE_OBJECTS ...... caching of objects for further use (default)
    CACHE_PERSISTENT ... persistent caching of objects into a local file

By default CACHE_OBJECTS is used. That means any changes to objects are
pushed to the server only when explicitly requested with the update()
method. Also, any object already loaded from the server is kept in
memory cache so that future references to that object are faster.


Persistent Cache
~~~~~~~~~~~~~~~~

Persistent cache (local proxy) further speeds up module performance. It
allows class caches to be stored in a file, load caches from a file, and
clear caches. This performance improvement is very helpful mainly for
immutable classes (for example User), where all users can be imported in
the beginning of a script and a lot of connections can be saved. To
activate this feature specify cache level and file name in the config:

    [cache]
    level = 3
    file = /home/user/.cache/nitrate

Cache expiration is a way how to prevent using probably obsoleted object
(for example caserun). Every class has its own default expiration time,
which can be adjusted in the config file (use lower case class names):

    [expiration]
    caserun = 60
    testcase = 600

Expiration time is given in seconds. In addition, there are two special
values which can be used:

    NEVER_CACHE .... no caching of certain class objects
    NEVER_EXPIRE ... cached objects never expire

Default expiration is set to 30 days for immutable classes and to 1 hour
for the rest with the exception of PlanType which is cached for ever and
CaseRun which is cached never.


MultiCall Support
~~~~~~~~~~~~~~~~~

MultiCall feature is used to encapsulate multiple calls to a remote
server into a single request. If enabled, TestPlan, TestRun, TestCase
and CaseRun objects will use MultiCall for updating their states (thus
speeding up the process). Example usage:

    multicall_start()
        for caserun in TestRun(12345):
            caserun.status = Status("IDLE")
            caserun.update()
    multicall_end()

When multicall_start() is called, update queries are not sent
immediately to server. Instead, they are queued and after
multicall_end() is called, all queries are sent to server in a batch.
"""

import os
import gzip
import pickle
import atexit
import datetime
import xmlrpclib
import nitrate.base as base
import nitrate.immutable as immutable
import nitrate.mutable as mutable
import nitrate.containers as containers
import nitrate.config as config

from nitrate.config import log, get_cache_level, set_cache_level
from nitrate.utils import pretty, listed, sliced, human
from nitrate.base import NitrateNone

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  MultiCall methods
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def multicall_start():
    """ Enter MultiCall mode and queue following xmlrpc calls """
    log.info("Starting multicall session, gathering updates...")
    base.Nitrate._multicall_proxy = xmlrpclib.MultiCall(base.Nitrate()._server)

def multicall_end():
    """ Execute xmlrpc call queue and exit MultiCall mode """
    log.info("Ending multicall session, sending to the server...")
    response = base.Nitrate._multicall_proxy()
    log.xmlrpc("Server response:")
    entries = 0
    for entry in response:
        log.xmlrpc(pretty(entry))
        entries += 1
    base.Nitrate._multicall_proxy = None
    base.Nitrate._requests += 1
    log.info("Multicall session finished, {0} completed".format(
            listed(entries, "update")))
    return response

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Cache Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Cache(object):
    """
    Persistent Cache

    Responsible for saving/loading all cached objects into/from local
    persistent cache saved in a file on disk.
    """

    # List of classes with persistent cache support
    _immutable = [immutable.Bug, immutable.Build, immutable.Version,
            immutable.Category, immutable.Component, immutable.PlanType,
            immutable.Product, immutable.Tag, immutable.User]
    _mutable = [mutable.TestCase, mutable.TestPlan, mutable.TestRun,
            mutable.CaseRun, mutable.CasePlan]
    _containers = [containers.CaseBugs, containers.CaseComponents,
            containers.CasePlans, containers.CaseRunBugs, containers.CaseTags,
            containers.ChildPlans, containers.PlanCasePlans,
            containers.PlanCases, containers.PlanRuns, containers.PlanTags,
            containers.RunCases, containers.RunCaseRuns, containers.RunTags]
    _classes = _immutable + _mutable + _containers

    # File path to the cache and open mode (read-only or read-write)
    _filename = None
    _lock = None
    _mode = None

    @staticmethod
    def setup(filename=None):
        """ Set cache filename and initialize expiration times """
        # Nothing to do when persistent caching is off
        if get_cache_level() < config.CACHE_PERSISTENT:
            return

        # Detect cache filename, argument first, then config
        if filename is not None:
            Cache._filename = filename
        else:
            try:
                Cache._filename = config.Config().cache.file
            except AttributeError:
                log.warn("Persistent caching off "
                        "(cache filename not found in the config)")
        Cache._lock = Cache._filename + ".lock"

        # Initialize user-defined expiration times from the config
        for klass in Cache._classes + [base.Nitrate, mutable.Mutable,
                containers.Container]:
            try:
                expiration = getattr(
                        config.Config().expiration, klass.__name__.lower())
            except AttributeError:
                continue
            # Convert from seconds, handle special values
            if isinstance(expiration, int):
                expiration = datetime.timedelta(seconds=expiration)
            elif expiration == "NEVER_EXPIRE":
                expiration = config.NEVER_EXPIRE
            elif expiration == "NEVER_CACHE":
                expiration = config.NEVER_CACHE
            # Give warning for invalid expiration values
            if isinstance(expiration, datetime.timedelta):
                klass._expiration = expiration
                log.debug("User defined expiration for {0}: {1}".format(
                        klass.__name__, expiration))
            else:
                log.warn("Invalid expiration time '{0}'".format(expiration))

    @staticmethod
    def save():
        """ Save caches to specified file """

        # Nothing to do when persistent caching is off
        if not Cache._filename or get_cache_level() < config.CACHE_PERSISTENT:
            return

        # Clear expired items and gather all caches into a single object
        Cache.expire()
        log.cache("Cache dump stats:\n" + Cache.stats().strip())
        data = {}
        for current_class in Cache._classes:
            # Put container classes into id-sleep
            if issubclass(current_class, containers.Container):
                for container in current_class._cache.itervalues():
                    container._sleep()
            data[current_class.__name__] = current_class._cache

        # Dump the cache object into file
        try:
            output_file = gzip.open(Cache._filename, 'wb')
            log.debug("Saving persistent cache into {0}".format(
                    Cache._filename))
            pickle.dump(data, output_file)
            output_file.close()
            log.debug("Persistent cache successfully saved")
        except IOError, error:
            log.error("Failed to save persistent cache ({0})".format(error))

    @staticmethod
    def load():
        """ Load caches from specified file """

        # Nothing to do when persistent caching is off
        if not Cache._filename or get_cache_level() < config.CACHE_PERSISTENT:
            return

        # Load the saved cache from file
        try:
            log.debug("Loading persistent cache from {0}".format(
                    Cache._filename))
            input_file = gzip.open(Cache._filename, 'rb')
            data = pickle.load(input_file)
            input_file.close()
        except EOFError:
            log.warn("Cache file empty, will fill it upon exit")
            return
        except IOError, error:
            if error.errno == 2:
                log.warn("Cache file not found, will create one on exit")
                return
            else:
                log.error("Failed to load the cache ({0})".format(error))
                log.error("Cache file: {0}".format(Cache._filename))
                log.warn("Going on but switching to CACHE_OBJECTS level")
                set_cache_level(config.CACHE_OBJECTS)
                return

        # Restore cache for immutable & mutable classes first
        for current_class in Cache._immutable + Cache._mutable:
            try:
                log.cache("Loading cache for {0}".format(
                        current_class.__name__))
                current_class._cache = data[current_class.__name__]
            except KeyError:
                log.cache("Failed to load cache for {0}, starting "
                        "with empty".format(current_class.__name__))
                current_class._cache = {}
        # Containers to be loaded last (to prevent object duplicates)
        for current_class in Cache._containers:
            try:
                log.cache("Loading cache for {0}".format(
                        current_class.__name__))
                current_class._cache = data[current_class.__name__]
            except KeyError:
                log.cache("Failed to load cache for {0}, starting "
                        "with empty".format(current_class.__name__))
                current_class._cache = {}
            # Wake up container objects from the id-sleep
            for container in current_class._cache.itervalues():
                container._wake()
        # Clear expired items and give a short summary for debugging
        Cache.expire()
        log.cache("Cache restore stats:\n" + Cache.stats().strip())

    @staticmethod
    def enter():
        """ Perform setup, create lock, load the cache """
        # Nothing to do when persistent caching is off
        if get_cache_level() < config.CACHE_PERSISTENT:
            return
        # Setup the cache
        Cache.setup()
        # Check for existing cache lock, set mode appropriately
        try:
            lock = open(Cache._lock)
            log.cache("Found lock {0}, opening read-only".format(Cache._lock))
            lock.close()
            Cache._mode = "read-only"
        except IOError:
            log.cache("Creating cache lock {0}".format(Cache._lock))
            lock = open(Cache._lock, "w")
            lock.write("{0}\n".format(os.getpid()))
            lock.close()
            Cache._mode = "read-write"
        # And finally load the cache
        Cache.load()

    @staticmethod
    def exit():
        """ Save the cache and remove the lock """
        # Nothing to do when persistent caching is off
        if get_cache_level() < config.CACHE_PERSISTENT:
            return
        # Skip cache save in read-only mode
        if Cache._mode == "read-only":
            log.cache("Skipping persistent cache save in read-only mode")
            return
        # Save the cache and remove the lock
        Cache.save()
        try:
            log.cache("Removing cache lock {0}".format(Cache._lock))
            os.remove(Cache._lock)
        except OSError, error:
            log.error("Failed to remove the cache lock {0} ({1})".format(
                    Cache._lock, error))

    @staticmethod
    def clear(classes=None):
        """
        Completely wipe out cache of all (or selected) classes

        Accepts class or a list of classes.
        """
        # Convert single class into a list
        if isinstance(classes, type):
            classes = [classes]
        log.cache("Wiping out {0} memory cache".format(
                "all objects'" if classes == None else listed(
                    [klass.__name__ for klass in classes])))
        # For each class re-initialize objects and remove from index
        for current_class in Cache._classes:
            if classes is not None and (current_class not in classes):
                continue
            for current_object in current_class._cache.itervalues():
                # Reset the object to the initial state
                current_object._init()
            current_class._cache = {}

    @staticmethod
    def expire():
        """
        Remove all out-of-date objects from the cache

        All expired objects are wiped out as well as those mutable
        objects which are in modified state (hold different information
        from what is on the server a thus could cause inconsistencies).
        Also all uninitialized objects are removed from the cache.
        """

        for current_class in Cache._classes:
            expired = []
            for id, current_object in current_class._cache.iteritems():
                expire = False
                # Check if object is uninitialized
                if (current_object._id is NitrateNone or
                        current_object._fetched is None):
                    log.cache("Wiping uninitialized {0} {1} from cache".format(
                            current_object.__class__.__name__,
                            current_object.identifier))
                    expire = True
                # Check if object is expired
                elif current_object._is_expired:
                    log.cache("Wiping expired {0} {1} from cache".format(
                            current_object.__class__.__name__,
                            current_object.identifier))
                    expire = True
                # Check if object is modified
                elif (isinstance(current_object, mutable.Mutable) and
                        current_object._modified):
                    log.cache("Wiping modified {0} {1} from cache".format(
                            current_object.__class__.__name__,
                            current_object.identifier))
                    expire = True
                if expire:
                    # Reset the object to the initial state
                    current_object._init()
                    expired.append(id)
            for id in expired:
                del current_class._cache[id]

    @staticmethod
    def update():
        """
        Update all modified mutable objects in the cache

        This method uses MultiCall to perform the update which can
        significantly speed up things when compared to updating each
        individual object separately.

        Note: The update is done in batches. The maximum number of objects
        updated at once is controlled by the global variable MULTICALL_MAX,
        by default set to 10 object per session."""

        for klass in Cache._mutable + Cache._containers:
            modified = [mutable for mutable in klass._cache.itervalues()
                    if mutable._modified]
            if not modified:
                continue
            log.info("Found {0} in the {1} cache, updating...".format(
                    listed(modified, "modified object"),
                    klass.__name__))
            for slice in sliced(modified, config.MULTICALL_MAX):
                multicall_start()
                for mutable in slice:
                    mutable.update()
                multicall_end()

    @staticmethod
    def stats():
        """ Return short stats about cached objects and expiration time """
        result = "class          objects       expiration\n"
        for current_class in sorted(Cache._classes, key=lambda x: x.__name__):
            result += "{0}{1}       {2}\n".format(
                   current_class.__name__.ljust(15),
                   str(len(set(current_class._cache.itervalues()))).rjust(7),
                   human(current_class._expiration))
        return result

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Cache Setup
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Setup up expiration times and load cache on module import
Cache.enter()
# Register callback to save the cache upon script exit
atexit.register(Cache.exit)
