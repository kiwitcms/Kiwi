# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
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
Kiwi TCMS class and internal utilities

Search support
~~~~~~~~~~~~~~

Multiple Kiwi TCMS classes provide the static method 'search' which takes
the search query in the Django QuerySet format which gives an easy
access to the foreign keys and basic search operators. For example:

    Product.search(name="Red Hat Enterprise Linux 6")
    TestPlan.search(name__contains="python")
    TestRun.search(manager__email='login@example.com'):
    TestCase.search(script__startswith='/CoreOS/python')

For the complete list of available operators see Django documentation:
https://docs.djangoproject.com/en/dev/ref/models/querysets/#field-lookups
"""

import datetime
import tcms_api.config as config
import tcms_api.xmlrpc as xmlrpc

from tcms_api.config import log, Config
from tcms_api.xmlrpc import TCMSError

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Internal Utilities
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def _getter(field):
    """
    Simple getter factory function.

    For given field generate getter function which calls self._fetch(), to
    initialize instance data if necessary, and returns self._field.
    """

    def getter(self):
        # Initialize the attribute unless already done
        if getattr(self, "_" + field) is TCMSNone:
            self._fetch()
        # Return self._field
        return getattr(self, "_" + field)

    return getter


def _setter(field):
    """
    Simple setter factory function.

    For given field return setter function which calls self._fetch(), to
    initialize instance data if necessary, updates the self._field and
    remembers modifed state if the value is changed.
    """

    def setter(self, value):
        # Initialize the attribute unless already done
        if getattr(self, "_" + field) is TCMSNone:
            self._fetch()
        # Update only if changed
        if getattr(self, "_" + field) != value:
            setattr(self, "_" + field, value)
            log.info("Updating {0}'s {1} to '{2}'".format(
                self.identifier, field, value))
            # Remember modified state if caching
            if config.get_cache_level() != config.CACHE_NONE:
                self._modified = True
            # Save the changes immediately otherwise
            else:
                self._update()

    return setter


def _idify(id):
    """
    Pack/unpack multiple ids into/from a single id

    List of ids is converted into a single id. Single id is converted
    into list of original ids. For example:

        _idify([1, 2]) ---> 1000000002
        _idify(1000000002) ---> [1, 2]

    This is used for indexing by fake internal id.
    """
    if isinstance(id, list):
        result = 0
        for value in id:
            result = result * config._MAX_ID + value
        return result
    elif isinstance(id, int):
        result = []
        while id > 0:
            remainder = id % config._MAX_ID
            id = int(id / config._MAX_ID)
            result.append(int(remainder))
        result.reverse()
        return result
    else:
        raise TCMSError("Invalid id for idifying: '{0}'".format(id))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TCMSNone Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class TCMSNone(object):
    """ Used for distinguishing uninitialized values from regular 'None' """
    pass


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TCMS Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class TCMS(object):
    """
    General TCMS Object.

    Takes care of initiating the connection to the TCMS server and
    parses user configuration.
    """

    # Unique object identifier. If not None ---> object is initialized
    # (all unknown attributes are set to special value TCMSNone)
    _id = None

    # Timestamp when the object data were fetched from the server.
    # If not None, all object attributes are filled with real data.
    _fetched = None

    # Default expiration for immutable objects is 1 month
    _expiration = datetime.timedelta(days=30)

    # List of all object attributes (used for init & expiration)
    _attributes = []

    _connection = None
    _requests = 0
    _identifier_width = 0

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TCMS Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Object identifier.")

    @property
    def identifier(self):
        """ Consistent identifier string """
        # Use id if known
        if self._id not in [None, TCMSNone]:
            id = self._id
        # When unknown use 'ID#UNKNOWN' or 'ID#UNKNOWN (name)'
        else:
            name = getattr(self, "_name", None)
            if name not in [None, TCMSNone]:
                id = "UNKNOWN ({0})".format(name)
            else:
                id = "UNKNOWN"
        return "{0}#{1}".format(
            self._prefix, str(id).rjust(self._identifier_width, "0"))

    @property
    def _server(self):
        """ Connection to the server """

        # Connect to the server unless already connected
        if TCMS._connection is None:
            log.debug("Contacting server {0}".format(Config().tcms.url))
            if hasattr(Config().tcms, 'use_mod_kerb') and Config().tcms.use_mod_kerb:
                # use Kerberos
                TCMS._connection = xmlrpc.TCMSKerbXmlrpc(
                    Config().tcms.url).server
            else:
                # use plain authentication otherwise
                TCMS._connection = xmlrpc.TCMSXmlrpc(
                    Config().tcms.username,
                    Config().tcms.password,
                    Config().tcms.url).server

        # Return existing connection
        TCMS._requests += 1
        return TCMS._connection

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # ID check
        if isinstance(id, int) or isinstance(id, str):
            return cls._cache[id], id

        # Check injet (initial object dictionary) for id
        if isinstance(id, dict):
            return cls._cache[id['id']], id["id"]

        raise KeyError

    @classmethod
    def _is_cached(cls, id):
        """
        Check whether objects are cached (initialized & fetched)

        Accepts object id, list of ids, object or a list of objects.
        Makes sure that the object is in the memory and has attached
        all attributes. For ids, cache index is checked for presence.
        """
        # Check fetch timestamp if object given
        if isinstance(id, TCMS):
            return id._fetched is not None
        # Check for presence in cache, make sure the object is fetched
        if isinstance(id, int) or isinstance(id, str):
            return id in cls._cache and cls._cache[id]._fetched is not None
        # Run recursively for each given id/object if list given
        if isinstance(id, list) or isinstance(id, set):
            return all(cls._is_cached(i) for i in id)
        # Something went wrong
        return False

    @property
    def _is_expired(self):
        """ Check if cached object has expired """
        return self._fetched is None or (
            datetime.datetime.now() - self._fetched) > self._expiration

    def _is_initialized(self, id_or_inject, **kwargs):
        """
        Check whether the object is initialized, handle names & injects

        Takes object id or inject (initial object dict), detects which
        of them was given, checks whether the object has already been
        initialized and returns tuple: (id, name, inject, initialized).
        """
        id = name = inject = None
        # Initial object dict
        if isinstance(id_or_inject, dict):
            inject = id_or_inject
        # Object identified by name
        elif isinstance(id_or_inject, str):
            name = id_or_inject
        # Regular object id
        else:
            id = id_or_inject
        # Initialized objects have the self._id attribute set
        if self._id is None:
            return id, name, inject, False
        # If inject given, fetch data from it (unless already fetched)
        if inject is not None and not self._fetched:
            self._fetch(inject, **kwargs)
        return id, name, inject, True

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TCMS Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, *args, **kwargs):
        """ Create a new object, handle caching if enabled """
        # No caching when turned of or class does not support it
        if (config.get_cache_level() < config.CACHE_OBJECTS or
                getattr(cls, "_cache", None) is None):
            return super(TCMS, cls).__new__(cls)
        # Look up cached object by id (or other arguments in kwargs)
        try:
            # If found, we get instance and key by which it was found
            instance, key = cls._cache_lookup(id, **kwargs)
            if isinstance(key, int):
                log.cache("Using cached {0} ID#{1}".format(cls.__name__, key))
            else:
                log.cache("Using cached {0} '{1}'".format(cls.__name__, key))
            return instance
        # Object not cached yet, create a new one and cache it
        except KeyError:
            new = super(TCMS, cls).__new__(cls)
            if isinstance(id, int):
                log.cache("Caching {0} ID#{1}".format(cls.__name__, id))
                cls._cache[id] = new
            elif isinstance(id, str) or "name" in kwargs:
                log.cache("Caching {0} '{1}'".format(
                    cls.__name__, (id or kwargs.get("name"))))
            return new

    def __init__(self, id=None, prefix="ID"):
        """ Initialize the object id, prefix and internal attributes """
        # Set up the prefix
        self._prefix = prefix
        # Initialize internal attributes and reset the fetch timestamp
        self._init()

        # Check and set the object id
        if id is None:
            self._id = TCMSNone
        elif isinstance(id, int):
            self._id = id
        else:
            try:
                self._id = int(id)
            except ValueError:
                raise TCMSError("Invalid {0} id: '{1}'".format(
                    self.__class__.__name__, id))

    def __str__(self):
        return "TCMS server: {0}\nTotal requests handled: {1}".format(
            Config().tcms.url, self._requests)

    def __eq__(self, other):
        """ Objects are compared based on their id """
        # Special handling for comparison with None
        if other is None:
            return False
        # We can only compare objects of the same type
        if self.__class__ != other.__class__:
            raise TCMSError("Cannot compare '{0}' with '{1}'".format(
                self.__class__.__name__, other.__class__.__name__))
        return self.id == other.id

    def __ne__(self, other):
        """ Objects are compared based on their id """
        return not(self == other)

    def __hash__(self):
        """ Use object id as the default hash """
        return self.id

    def __repr__(self):
        """ Object(id) or Object('name') representation """
        # Use the object id by default, name (if available) otherwise
        if self._id is not TCMSNone:
            id = self._id
        elif getattr(self, "_name", TCMSNone) is not TCMSNone:
            id = "'{0}'".format(self._name)
        else:
            id = "<unknown>"
        return "{0}({1})".format(self.__class__.__name__, id)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TCMS Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _init(self):
        """ Set all object attributes to TCMSNone, reset fetch timestamp """
        # Each class is expected to have a list of attributes defined
        for attribute in self._attributes:
            setattr(self, "_" + attribute, TCMSNone)
        # And reset the fetch timestamp
        self._fetched = None

    def _fetch(self, inject=None):
        """ Fetch object data from the server """
        # This is to be implemented by respective class.
        # Here we just save the timestamp when data were fetched.
        self._fetched = datetime.datetime.now()
        # Store the initial object dict for possible future use
        self._inject = inject

    def _index(self, *keys):
        """ Index self into the class cache if caching enabled """
        # Skip indexing completely when caching off
        if config.get_cache_level() < config.CACHE_OBJECTS:
            return
        # Index by ID
        if self._id is not TCMSNone:
            self.__class__._cache[self._id] = self
        # Index each given key
        for key in keys:
            self.__class__._cache[key] = self
