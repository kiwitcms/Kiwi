# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   This is a Python API for the Nitrate test case management system.
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

""" High-level API for the Nitrate test case management system.  """

import os
import re
import sys
import gzip
import math
import time
import types
import pickle
import atexit
import random
import logging
import optparse
import tempfile
import unittest
import datetime
import xmlrpclib
import unicodedata
import ConfigParser
from pprint import pformat as pretty
from xmlrpc import NitrateError, NitrateKerbXmlrpc, NitrateXmlrpc


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Global Constants
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

NEVER_CACHE = datetime.timedelta(seconds=0)
NEVER_EXPIRE = datetime.timedelta(days=365)

CACHE_NONE = 0
CACHE_CHANGES = 1
CACHE_OBJECTS = 2
CACHE_PERSISTENT = 3

COLOR_ON = 1
COLOR_OFF = 0
COLOR_AUTO = 2

LOGGING_CACHE = 7
LOGGING_XMLRPC = 3
LOGGING_ALL = 1
LOGGING_COLORS = {
        logging.ERROR: "red",
        logging.WARN: "yellow",
        logging.INFO: "blue",
        logging.DEBUG: "green",
        LOGGING_CACHE: "cyan",
        LOGGING_XMLRPC: "magenta",
        }

# Max number of objects updated by multicall at once when using Cache.update()
MULTICALL_MAX = 10

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Logging
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#  Recommended debug levels:
#
#  log.info(msg) ..... high-level info, useful for tracking the progress
#  log.debug(msg) .... low-level info with details useful for investigation
#  log.cache(msg) .... stuff related to caching and object initialization
#  log.xmlrpc(msg) ... data communicated to or from the xmlrpc server

# Global logger and current log level
log = None
_log_level = logging.WARN

class ColoredFormatter(logging.Formatter):
    """ Custom color formatter for logging """
    def format(self, record):
        # Handle custom log level names
        if record.levelno == LOGGING_XMLRPC:
            levelname = "XMLRPC"
        elif record.levelno == LOGGING_CACHE:
            levelname = "CACHE"
        else:
            levelname = record.levelname
        # Map log level to appropriate color
        try:
            colour = LOGGING_COLORS[record.levelno]
        except:
            colour = "black"
        # Color the log level, use brackets when coloring off
        if _color:
            level = color(" " + levelname + " ", "lightwhite", colour)
        else:
            level = "[{0}]".format(levelname)
        return "{0} {1}".format(level, record.getMessage())

def _create_logger():
    """ Create nitrate logger """
    global log
    # Create logger, handler and formatter
    log = logging.getLogger('nitrate')
    handler = logging.StreamHandler()
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(ColoredFormatter())
    log.addHandler(handler)
    # Save log levels in the logger itself (backward compatibility)
    for level in "CRITICAL DEBUG ERROR FATAL INFO NOTSET WARN WARNING".split():
        setattr(log, level, getattr(logging, level))
    # Additional logging constants and methods for cache and xmlrpc
    log.XMLRPC = LOGGING_XMLRPC
    log.CACHE = LOGGING_CACHE
    log.ALL = LOGGING_ALL
    log.cache = lambda message: log.log(LOGGING_CACHE, message)
    log.xmlrpc = lambda message: log.log(LOGGING_XMLRPC, message)

def set_log_level(level=None):
    """
    Set the default log level

    If the level is not specified environment variable DEBUG is used
    with the following meaning:

        DEBUG=0 ... nitrate.log.WARN (default)
        DEBUG=1 ... nitrate.log.INFO
        DEBUG=2 ... nitrate.log.DEBUG
        DEBUG=3 ... nitrate.log.CACHE
        DEBUG=4 ... nitrate.log.XMLRPC
        DEBUG=5 ... nitrate.log.ALL (log all messages)
    """

    global _log_level
    mapping = {
            0: logging.WARN,
            1: logging.INFO,
            2: logging.DEBUG,
            3: LOGGING_CACHE,
            4: LOGGING_XMLRPC,
            5: LOGGING_ALL,
            }
    # If level specified, use given
    if level is not None:
        _log_level = level
    # Otherwise attempt to detect from the environment
    else:
        try:
            _log_level = mapping[int(os.environ["DEBUG"])]
        except StandardError:
            _log_level = logging.WARN
    if log is None:
        _create_logger()
    log.setLevel(_log_level)

def get_log_level():
    """ Get the current log level """
    return _log_level

def setLogLevel(level=None):
    """ Deprecated, use set_log_level() instead """
    log.warn("Deprecated call setLogLevel(), use set_log_level() instead")
    set_log_level(level)

def info(message, newline=True):
    """ Log provided info message to the standard error output """
    sys.stderr.write(message + ("\n" if newline else ""))

set_log_level()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Config Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Config(object):
    """ User configuration. """

    # Config path
    path = os.path.expanduser("~/.nitrate")

    # Minimal config example
    example = ("Please, provide at least a minimal config file {0}:\n"
                "[nitrate]\n"
                "url = https://nitrate.server/xmlrpc/".format(path))

    def __init__(self):
        """ Initialize the configuration """

        # Trivial class for sections
        class Section(object): pass

        # Try system settings when the config does not exist in user directory
        if not os.path.exists(self.path):
            log.debug("User config file not found, trying /etc/nitrate.conf")
            self.path = "/etc/nitrate.conf"
        if not os.path.exists(self.path):
            log.error(self.example)
            raise NitrateError("No config file found")

        # Parse the config
        try:
            parser = ConfigParser.SafeConfigParser()
            parser.read([self.path])
            for section in parser.sections():
                # Create a new section object for each section
                setattr(self, section, Section())
                # Set its attributes to section contents (adjust types)
                for name, value in parser.items(section):
                    try: value = int(value)
                    except: pass
                    if value == "True": value = True
                    if value == "False": value = False
                    setattr(getattr(self, section), name, value)
        except ConfigParser.Error:
            log.error(self.example)
            raise NitrateError(
                    "Cannot read the config file")

        # Make sure the server URL is set
        try:
            self.nitrate.url is not None
        except AttributeError:
            log.error(self.example)
            raise NitrateError("No url found in the config file")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Coloring
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_color_mode = COLOR_AUTO
_color = True

def color(text, color=None, background=None, light=False):
    """ Return text in desired color if coloring enabled """

    colors = {"black": 30, "red": 31, "green": 32, "yellow": 33,
            "blue": 34, "magenta": 35, "cyan": 36, "white": 37}

    # Prepare colors (strip 'light' if present in color)
    if color and color.startswith("light"):
        light = True
        color = color[5:]
    color = color and ";{0}".format(colors[color]) or ""
    background = background and ";{0}".format(colors[background] + 10) or ""
    light = light and 1 or 0

    # Starting and finishing sequence
    start = "\033[{0}{1}{2}m".format(light , color, background)
    finish = "\033[1;m"

    if _color:
        return "".join([start, text, finish])
    else:
        return text

def set_color_mode(mode=None):
    """
    Set the coloring mode

    If enabled, some objects (like case run Status) are printed in color
    to easily spot failures, errors and so on. By default the feature is
    enabled when script is attached to a terminal. Possible values are:

        COLOR_ON ..... coloring enabled
        COLOR_OFF .... coloring disabled
        COLOR_AUTO ... enabled if terminal detected (default)

    Environment variable COLOR can be used to set up the coloring to the
    desired mode without modifying code.
    """

    global _color
    global _color_mode
    if mode is None:
        try:
            mode = int(os.environ["COLOR"])
        except StandardError:
            mode = COLOR_AUTO
    elif mode < 0 or mode > 2:
        raise NitrateError("Invalid color mode '{0}'".format(mode))
    _color_mode = mode

    if mode == COLOR_AUTO:
        _color = sys.stdout.isatty()
    else:
        _color = mode == 1

    log.debug("Coloring {0}".format(_color and "enabled" or "disabled"))

def get_color_mode():
    """ Get the current color mode """
    return _color_mode

def setColorMode(mode=None):
    """ Deprecated, use set_color_mode() instead """
    log.warn("Deprecated call setColorMode(), use set_color_mode() instead")
    set_color_mode(mode)

set_color_mode()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Caching
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_cache_level = CACHE_OBJECTS

def set_cache_level(level=None):
    """
    Set the caching level

    If the level parameter is not specified environment variable CACHE
    and configuration section [cache] are inspected. There are four cache
    levels available. See module documentation for detailed description.
    """

    global _cache_level
    if level is None:
        # Attempt to detect the level from the environment
        try:
            _cache_level = int(os.environ["CACHE"])
        except StandardError:
            # Inspect the [cache] sectin of the config file
            try:
                _cache_level = Config().cache.level
            except AttributeError:
                _cache_level = CACHE_OBJECTS
    elif level >= 0 and level <= 3:
        _cache_level = level
    else:
        raise NitrateError("Invalid cache level '{0}'".format(level))
    log.debug("Caching on level {0}".format(_cache_level))

def get_cache_level():
    """ Get the current caching level """
    return _cache_level

def setCacheLevel(level=None):
    """ Deprecated, use set_cache_level() instead """
    log.warn("Deprecated call setCacheLevel(), use set_cache_level() instead")
    set_cache_level(level)

set_cache_level()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Default Getter & Setter
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _getter(field):
    """
    Simple getter factory function.

    For given field generate getter function which calls self._fetch(), to
    initialize instance data if necessary, and returns self._field.
    """

    def getter(self):
        # Initialize the attribute unless already done
        if getattr(self, "_" + field) is NitrateNone:
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
        if getattr(self, "_" + field) is NitrateNone:
            self._fetch()
        # Update only if changed
        if getattr(self, "_" + field) != value:
            setattr(self, "_" + field, value)
            log.info(u"Updating {0}'s {1} to '{2}'".format(
                    self.identifier, field, value))
            # Remember modified state if caching
            if _cache_level != CACHE_NONE:
                self._modified = True
            # Save the changes immediately otherwise
            else:
                self._update()

    return setter


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Various Utilities
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def listed(items, singular=None, plural=None, max=None, quote=""):
    """
    Convert an iterable into a nice, human readable list or description.

    listed(range(1)) .................... 0
    listed(range(2)) .................... 0 and 1
    listed(range(3), quote='"') ......... "0", "1" and "2"
    listed(range(4), max=3) ............. 0, 1, 2 and 1 more
    listed(range(5), 'number', max=3) ... 0, 1, 2 and 2 more numbers
    listed(range(6), 'category') ........ 6 categories
    listed(7, "leaf", "leaves") ......... 7 leaves

    If singular form is provided but max not set the description-only
    mode is activated as shown in the last two examples. Also, an int
    can be used in this case to get a simple inflection functionality.
    """

    # Convert items to list if necessary
    if isinstance(items, int):
        items = range(items)
    elif not isinstance(items, list):
        items = list(items)
    more = " more"
    # Description mode expected when singular provided but no maximum set
    if singular is not None and max is None:
        max = 0
        more = ""
    # Set the default plural form
    if singular is not None and plural is None:
        if singular.endswith("y") and not singular.endswith("ay"):
            plural = singular[:-1] + "ies"
        elif singular.endswith("s"):
            plural = singular + "es"
        else:
            plural = singular + "s"
    # Convert to strings and optionally quote each item
    items = ["{0}{1}{0}".format(quote, item) for item in items]

    # Select the maximum of items and describe the rest if max provided
    if max is not None:
        # Special case when the list is empty (0 items)
        if max == 0 and len(items) == 0:
            return "0 {0}".format(plural)
        # Cut the list if maximum exceeded
        if len(items) > max:
            rest = len(items[max:])
            items = items[:max]
            if singular is not None:
                more += " {0}".format(singular if rest == 1 else plural)
            items.append("{0}{1}".format(rest, more))

    # For two and more items use 'and' instead of the last comma
    if len(items) < 2:
        return "".join(items)
    else:
        return ", ".join(items[0:-2] + [" and ".join(items[-2:])])

def unlisted(text):
    """ Convert human readable list into python list """
    return re.split("\s*,\s*|\s+and\s+|\s+", text)

def sliced(loaf, max):
    """
    Slice loafs into slices of maximum width

    Accepts large list (loaf) and cuts it into small lists of roughly
    even size (slices) less than max. Then yields each slice.
    """
    # Nothing to slice when the loaf is empty
    if not loaf:
        yield []
        return
    # Count necessary number of slices and the optimal slice width
    slices = math.ceil(1.0 * len(loaf) / max)
    width = int(math.ceil(len(loaf) / slices))
    # Yield individual slices
    while loaf:
        slice, loaf = loaf[0:width], loaf[width:]
        yield slice

def human(time):
    """ Convert timedelta into a human readable format """
    count = {}
    count["year"] = time.days / 365
    count["month"] = (time.days - 365 * count["year"]) / 30
    count["day"] = 0 if count["year"] > 0 else time.days % 30
    count["hour"] = time.seconds / 3600
    count["minute"] = (time.seconds - 3600 * count["hour"]) / 60
    count["second"] = (
            time.seconds - 3600 * count["hour"] - 60 * count["minute"])
    return listed([
            listed(count[period], period)
            for period in ["year", "month", "day", "hour", "minute", "second"]
            if count[period] > 0
            or time.seconds == time.days == 0 and period == "second"])

def ascii(text):
    """ Transliterate special unicode characters into pure ascii. """
    if not isinstance(text, unicode): text = unicode(text)
    return unicodedata.normalize('NFKD', text).encode('ascii','ignore')

def header(text, width=70):
    """ Print a simple header (text with tilde underline) """
    return "\n{0}\n{1}".format(text, width * "~")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Internal Utilities
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Maximum id value (used for idifying)
_MAX_ID = 1000000000

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
            result = result * _MAX_ID + value
        return result
    elif isinstance(id, int):
        result = []
        while id > 0:
            remainder = id % _MAX_ID
            id = id / _MAX_ID
            result.append(int(remainder))
        result.reverse()
        return result
    else:
        raise NitrateError("Invalid id for idifying: '{0}'".format(id))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  MultiCall methods
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def multicall_start():
    """ Enter MultiCall mode and queue following xmlrpc calls """
    log.info("Starting multicall session, gathering updates...")
    Nitrate._multicall_proxy = xmlrpclib.MultiCall(Nitrate()._server)

def multicall_end():
    """ Execute xmlrpc call queue and exit MultiCall mode """
    log.info("Ending multicall session, sending to the server...")
    response = Nitrate._multicall_proxy()
    log.xmlrpc("Server response:")
    entries = 0
    for entry in response:
        log.xmlrpc(pretty(entry))
        entries += 1
    Nitrate._multicall_proxy = None
    Nitrate._requests += 1
    log.info("Multicall session finished, {0} completed".format(
            listed(entries, "update")))
    return response

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Internal Utilities
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _print_time(elapsed_time):
    converted_time = str(datetime.timedelta(seconds=elapsed_time)).split('.')
    sys.stderr.write("{0} ... ".format(converted_time[0]))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Nitrate None Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class NitrateNone(object):
    """ Used for distinguishing uninitialized values from regular 'None'. """
    pass


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Nitrate Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Nitrate(object):
    """
    General Nitrate Object.

    Takes care of initiating the connection to the Nitrate server and
    parses user configuration.
    """

    # Unique object identifier. If not None ---> object is initialized
    # (all unknown attributes are set to special value NitrateNone)
    _id = None

    # Timestamp when the object data were fetched from the server.
    # If not None, all object attributes are filled with real data.
    _fetched = None

    # Default expiration for immutable objects is 1 month
    _expiration = datetime.timedelta(days=30)

    # List of all object attributes (used for init & expiration)
    _attributes = []

    _connection = None
    _settings = None
    _requests = 0
    _multicall_proxy = None
    _identifier_width = 0

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Object identifier.")

    @property
    def identifier(self):
        """ Consistent identifier string. """
        id = self._id if self._id is not None else "UNKNOWN"
        return "{0}#{1}".format(
                self._prefix, str(id).rjust(self._identifier_width, "0"))

    @property
    def _config(self):
        """ User configuration (expected in ~/.nitrate). """

        # Read the config file (unless already done)
        if Nitrate._settings is None:
            Nitrate._settings = Config()

        # Return the settings
        return Nitrate._settings

    @property
    def _server(self):
        """ Connection to the server. """

        # Connect to the server unless already connected
        if Nitrate._connection is None:
            log.debug(u"Contacting server {0}".format(
                    self._config.nitrate.url))
            # Plain authentication if username & password given
            try:
                Nitrate._connection = NitrateXmlrpc(
                        self._config.nitrate.username,
                        self._config.nitrate.password,
                        self._config.nitrate.url).server
            # Kerberos otherwise
            except AttributeError:
                Nitrate._connection = NitrateKerbXmlrpc(
                        self._config.nitrate.url).server

        # Return existing connection
        Nitrate._requests += 1
        return Nitrate._connection

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # ID check
        if isinstance(id, int) or isinstance(id, basestring):
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
        if isinstance(id, Nitrate):
            return id._fetched is not None
        # Check for presence in cache, make sure the object is fetched
        if isinstance(id, int) or isinstance(id, basestring):
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
        elif isinstance(id_or_inject, basestring):
            name =  id_or_inject
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

    @property
    def _multicall(self):
        """
        Enqueue xmlrpc calls if MultiCall enabled otherwise send directly

        If MultiCall mode enabled, put xmlrpc calls to the queue, otherwise
        send them directly to server.
        """
        if Nitrate._multicall_proxy is not None:
            return self._multicall_proxy
        else:
            return self._server

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, *args, **kwargs):
        """ Create a new object, handle caching if enabled. """

        if _cache_level < CACHE_OBJECTS or cls not in Cache._classes:
            return super(Nitrate, cls).__new__(cls)

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
            new = super(Nitrate, cls).__new__(cls)
            if isinstance(id, int):
                log.cache("Caching {0} ID#{1}".format(cls.__name__, id))
                cls._cache[id] = new
            elif isinstance(id, basestring) or "name" in kwargs:
                log.cache("Caching {0} '{1}'".format(
                        cls.__name__, (id or kwargs.get("name"))))
            return new

    def __init__(self, id=None, prefix="ID"):
        """ Initialize the object id, prefix and internal attributes. """
        # Set up the prefix
        self._prefix = prefix
        # Initialize internal attributes and reset the fetch timestamp
        self._init()

        # Check and set the object id
        if id is None:
            self._id = NitrateNone
        elif isinstance(id, int):
            self._id = id
        else:
            try:
                self._id = int(id)
            except ValueError:
                raise NitrateError("Invalid {0} id: '{1}'".format(
                        self.__class__.__name__, id))

    def __str__(self):
        """ Provide ascii string representation. """
        return ascii(self.__unicode__())

    def __unicode__(self):
        """ Short summary about the connection. """
        return u"Nitrate server: {0}\nTotal requests handled: {1}".format(
                self._config.nitrate.url, self._requests)

    def __eq__(self, other):
        """ Objects are compared based on their id. """
        # Special handling for comparison with None
        if other is None:
            return False
        # We can only compare objects of the same type
        if self.__class__ != other.__class__:
            raise NitrateError("Cannot compare '{0}' with '{1}'".format(
                self.__class__.__name__, other.__class__.__name__))
        return self.id == other.id

    def __ne__(self, other):
        """ Objects are compared based on their id. """
        return not(self == other)

    def __hash__(self):
        """ Use object id as the default hash. """
        return self.id

    def __repr__(self):
        """ Object(id) or Object('name') representation. """
        # Use the object id by default, name (if available) otherwise
        if self._id is not NitrateNone:
            id = self._id
        elif getattr(self, "_name", NitrateNone) is not NitrateNone:
            id = "'{0}'".format(self._name)
        else:
            id = "<unknown>"
        return "{0}({1})".format(self.__class__.__name__, id)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _init(self):
        """ Set all object attributes to NitrateNone, reset fetch timestamp """
        # Each class is expected to have a list of attributes defined
        for attribute in self._attributes:
            setattr(self, "_" + attribute, NitrateNone)
        # And reset the fetch timestamp
        self._fetched = None

    def _fetch(self, inject=None):
        """ Fetch object data from the server. """
        # This is to be implemented by respective class.
        # Here we just save the timestamp when data were fetched.
        self._fetched = datetime.datetime.now()
        # Store the initial object dict for possible future use
        self._inject = inject

    def _index(self, *keys):
        """ Index self into the class cache if caching enabled """
        # Skip indexing completely when caching off
        if get_cache_level() < CACHE_OBJECTS:
            return
        # Index by ID
        if self._id is not NitrateNone:
            self.__class__._cache[self._id] = self
        # Index each given key
        for key in keys:
            self.__class__._cache[key] = self

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Utils Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Utils(Nitrate):
    """ Tests for utility functions """

    class _test(unittest.TestCase):
        def test_listed(self):
            """ Function listed() sanity """
            self.assertEqual(listed(range(1)), "0")
            self.assertEqual(listed(range(2)), "0 and 1")
            self.assertEqual(listed(range(3), quote='"'), '"0", "1" and "2"')
            self.assertEqual(listed(range(4), max=3), "0, 1, 2 and 1 more")
            self.assertEqual(listed(range(5), 'number', max=3),
                    "0, 1, 2 and 2 more numbers")
            self.assertEqual(listed(range(6), 'category'), "6 categories")
            self.assertEqual(listed(7, "leaf", "leaves"), "7 leaves")

        def test_unlisted(self):
            """ Function unlisted() sanity """
            self.assertEqual(unlisted("1, 2 and 3"), ["1", "2", "3"])
            self.assertEqual(unlisted("1, 2, 3"), ["1", "2", "3"])
            self.assertEqual(unlisted("1 2 3"), ["1", "2", "3"])

        def test_sliced(self):
            """ Function sliced() sanity """
            loaf = range(9)
            self.assertEqual(list(sliced(loaf, 9)), [loaf])
            self.assertEqual(
                    list(sliced(loaf, 5)), [[0, 1, 2, 3, 4], [5, 6, 7, 8]])
            self.assertEqual(
                    list(sliced(loaf, 3)), [[0, 1, 2], [3, 4, 5], [6, 7, 8]])

        def test_get_set_log_level(self):
            """ Get & set the logging level """
            global _log_level
            original = _log_level
            for level in [log.DEBUG, log.WARN, log.ERROR]:
                set_log_level(level)
                self.assertEqual(_log_level, level)
                self.assertEqual(get_log_level(), level)
            _log_level = original

        def test_get_set_cache_level(self):
            """ Get & set the caching level """
            global _cache_level
            original = _cache_level
            for level in [CACHE_NONE, CACHE_CHANGES, CACHE_OBJECTS]:
                set_cache_level(level)
                self.assertEqual(_cache_level, level)
                self.assertEqual(get_cache_level(), level)
            _cache_level = original

        def test_get_set_color_mode(self):
            """ Get & set the color mode """
            global _color_mode
            original = _color_mode
            for mode in [COLOR_ON, COLOR_OFF, COLOR_AUTO]:
                set_color_mode(mode)
                self.assertEqual(_color_mode, mode)
                self.assertEqual(get_color_mode(), mode)
            _color_mode = original


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Build Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Build(Nitrate):
    """ Product build. """

    # Local cache of Build
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["name", "product"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Build id.")
    name = property(_getter("name"), doc="Build name.")
    product = property(_getter("product"), doc="Relevant product.")

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """

        # Name and product check
        if "product" in kwargs and ("name" in kwargs or "build" in kwargs):
            product = kwargs.get("product")
            if isinstance(product, Product):
                product = product.name
            name = kwargs.get("name", kwargs.get("build"))
            return cls._cache["{0}---in---{1}".format(name, product)], name

        return super(Build, cls)._cache_lookup(id, **kwargs)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None, product=None, **kwargs):
        """ Initialize by build id or product and build name. """

        # Backward compatibility for 'build' argument (now called 'name')
        name = name if name is not None else kwargs.get("build")

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id or name)
        if initialized: return
        Nitrate.__init__(self, id)

        # If inject given, fetch build data from it
        if inject:
            self._fetch(inject)
        # Initialized by build name and product
        elif name is not None and product is not None:
            self._name = name
            # Detect product format
            if isinstance(product, Product):
                self._product = product
            else:
                self._product = Product(product)
            # Index by name-product (only when the product name is known)
            if self.product._name is not NitrateNone:
                self._index("{0}---in---{1}".format(
                        self.name, self.product.name))
        # Otherwise just check that the id was provided
        elif not id:
            raise NitrateError("Need either build id or both build name "
                    "and product to initialize the Build object.")

    def __unicode__(self):
        """ Build name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing build data. """
        Nitrate._fetch(self, inject)
        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing build ID#{0} inject".format(
                    inject["build_id"]))
        # Search by build id
        elif self._id is not NitrateNone:
            try:
                log.info("Fetching build " + self.identifier)
                inject = self._server.Build.get(self.id)
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError(
                        "Cannot find build for " + self.identifier)
        # Search by build name and product
        else:
            try:
                log.info(u"Fetching build '{0}' of '{1}'".format(
                        self.name, self.product.name))
                inject = self._server.Build.check_build(
                        self.name, self.product.id)
                self._id = inject["build_id"]
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError("Build '{0}' not found in '{1}'".format(
                    self.name, self.product.name))

        # Initialize data from the inject and index into cache
        log.debug("Initializing Build ID#{0}".format(inject["build_id"]))
        log.xmlrpc(pretty(inject))
        self._inject = inject
        self._id = inject["build_id"]
        self._name = inject["name"]
        self._product = Product(
                {"id": inject["product_id"], "name": inject["product"]})
        self._index("{0}---in---{1}".format(self.name, self.product.name))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Clear cache, save cache level and initialize test data """
            self.product = Nitrate()._config.product
            self.build = Nitrate()._config.build
            self.requests = Nitrate._requests
            self.cache_level = get_cache_level()
            Cache.clear()

        def tierDown(self):
            """ Restore cache level """
            set_cache_level(self.cache_level)

        def test_fetch_by_id(self):
            """ Fetch by id """
            build = Build(self.build.id)
            self.assertEqual(build.name, self.build.name)

        def test_fetch_by_name_and_product(self):
            """ Fetch by name and product """
            # Named arguments
            build = Build(name=self.build.name, product=self.product.name)
            self.assertEqual(build.id, self.build.id)
            # Backward compatibility
            build = Build(build=self.build.name, product=self.product.name)
            self.assertEqual(build.id, self.build.id)

        def test_cache_none(self):
            """ Cache none """
            set_cache_level(CACHE_NONE)
            build1 = Build(self.build.id)
            self.assertEqual(build1.name, self.build.name)
            build2 = Build(self.build.id)
            self.assertEqual(build2.name, self.build.name)
            self.assertEqual(build1, build2)
            self.assertEqual(Nitrate._requests, self.requests + 2)

        def test_cache_objects(self):
            """ Cache objects """
            set_cache_level(CACHE_OBJECTS)
            build1 = Build(self.build.id)
            self.assertEqual(build1.name, self.build.name)
            build2 = Build(self.build.id)
            self.assertEqual(build2.name, self.build.name)
            self.assertEqual(build1, build2)
            self.assertEqual(id(build1), id(build2))
            self.assertEqual(Nitrate._requests, self.requests + 1)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Category Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Category(Nitrate):
    """ Test case category. """

    # Local cache of Category objects indexed by category id
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["name", "product", "description"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Category id.")
    name = property(_getter("name"), doc="Category name.")
    product = property(_getter("product"), doc="Relevant product.")
    description = property(_getter("description"), doc="Category description.")

    @property
    def synopsis(self):
        """ Short category summary (including product info). """
        return "{0}, {1}".format(self.name, self.product)

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """

        # Name and product check
        if "product" in kwargs and ("name" in kwargs or "category" in kwargs):
            product = kwargs.get("product")
            if isinstance(product, Product):
                product = product.name
            name = kwargs.get("name", kwargs.get("category"))
            return cls._cache["{0}---in---{1}".format(name, product)], name

        return super(Category, cls)._cache_lookup(id, **kwargs)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None, product=None, **kwargs):
        """ Initialize by category id or category name and product """

        # Backward compatibility for 'category' argument (now called 'name')
        name = name if name is not None else kwargs.get("category")

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id or name)
        if initialized: return
        Nitrate.__init__(self, id)

        # If inject given, fetch tag data from it
        if inject:
            self._fetch(inject)
        # Initialized by category name and product
        elif name is not None and product is not None:
            self._name = name
            # Detect product format
            if isinstance(product, Product):
                self._product = product
            else:
                self._product = Product(product)
            # Index by name-product (only when the product name is known)
            if self.product._name is not NitrateNone:
                self._index("{0}---in---{1}".format(
                        self.name, self.product.name))
        # Otherwise just check that the id was provided
        elif not id:
            raise NitrateError("Need either category id or both category "
                    "name and product to initialize the Category object.")

    def __unicode__(self):
        """ Category name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing category data. """
        Nitrate._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing category ID#{0} inject".format(inject["id"]))
        # Search by category id
        elif self._id is not NitrateNone:
            try:
                log.info("Fetching category {0}".format(self.identifier))
                inject = self._server.Product.get_category(self.id)
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError(
                        "Cannot find category for " + self.identifier)
        # Search by category name and product
        else:
            try:
                log.info(u"Fetching category '{0}' of '{1}'".format(
                        self.name, self.product.name))
                inject = self._server.Product.check_category(
                        self.name, self.product.id)
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError("Category '{0}' not found in"
                        " '{1}'".format(self.name, self.product.name))

        # Initialize data from the inject and index into cache
        log.debug("Initializing category ID#{0}".format(inject["id"]))
        log.xmlrpc(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["name"]
        self._product = Product(
                {"id": inject["product_id"], "name": inject["product"]})
        self._index("{0}---in---{1}".format(self.name, self.product.name))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):

        def setUp(self):
            """ Clear cache, save cache level and initialize test data """
            Cache.clear()
            self.cache_level = get_cache_level()
            self.product = Nitrate()._config.product
            self.category = Nitrate()._config.category
            self.requests = Nitrate._requests

        def tierDown(self):
            """ Restore cache level """
            set_cache_level(self.cache_level)

        def test_fetch_by_id(self):
            """ Fetch by id """
            category = Category(self.category.id)
            self.assertEqual(category.name, self.category.name)

        def test_fetch_by_name_and_product(self):
            """ Fetch by name and product """
            # Named arguments
            category = Category(
                    name=self.category.name, product=self.product.name)
            self.assertEqual(category.id, self.category.id)
            # Backward compatibility
            category = Category(
                    category=self.category.name, product=self.product.name)
            self.assertEqual(category.id, self.category.id)

        def test_cache_objects(self):
            """ Cache objects """
            set_cache_level(CACHE_OBJECTS)
            # The first round (fetch category data from server)
            category = Category(self.category.id)
            self.assertEqual(category.name, self.category.name)
            self.assertEqual(Nitrate._requests, self.requests + 1)
            # The second round (there should be no more requests)
            category = Category(self.category.id)
            self.assertEqual(category.name, self.category.name)
            self.assertEqual(Nitrate._requests, self.requests + 1)

        def test_cache_none(self):
            """ Cache none """
            set_cache_level(CACHE_NONE)
            # The first round (fetch category data from server)
            category = Category(self.category.id)
            self.assertEqual(category.name, self.category.name)
            self.assertEqual(Nitrate._requests, self.requests + 1)
            # The second round (there should be another request)
            category = Category(self.category.id)
            self.assertEqual(category.name, self.category.name)
            self.assertEqual(Nitrate._requests, self.requests + 2)

        def test_invalid_category(self):
            """ Invalid category should raise exception """
            def fun():
                Category(category="Bad", product=self.product.name).id
            original_log_level = get_log_level()
            set_log_level(log.CRITICAL)
            self.assertRaises(NitrateError, fun)
            set_log_level(original_log_level)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Type Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanType(Nitrate):
    """ Plan type """

    # Local cache of PlanType objects indexed by plan type id
    _cache = {}

    # By default we cache PlanType objects for ever
    _expiration = NEVER_EXPIRE

    # List of all object attributes (used for init & expiration)
    _attributes = ["name"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Type Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Test plan type id")
    name = property(_getter("name"), doc="Test plan type name")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Type Decorated
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # Search cache by plan type name
        if "name" in kwargs:
            return cls._cache[kwargs["name"]], kwargs["name"]
        # Othewise perform default search by id
        return super(PlanType, cls)._cache_lookup(id, **kwargs)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Type Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None):
        """ Initialize by test plan type id or name """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id or name)
        if initialized: return
        Nitrate.__init__(self, id)

        # If inject given, fetch data from it
        if inject:
            self._fetch(inject)
        # Initialize by name
        elif name is not None:
            self._name = name
            self._index(name)
        # Otherwise just check that the test plan type id was provided
        elif not id:
            raise NitrateError(
                    "Need either id or name to initialize the PlanType object")

    def __unicode__(self):
        """ PlanType name for printing """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Type Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing test plan type data """
        Nitrate._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing PlanType ID#{0} inject".format(inject["id"]))
        # Search by test plan type id
        elif self._id is not NitrateNone:
            try:
                log.info("Fetching test plan type " + self.identifier)
                inject = self._server.TestPlan.get_plan_type(self.id)
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError(
                        "Cannot find test plan type for " + self.identifier)
        # Search by test plan type name
        else:
            try:
                log.info(u"Fetching test plan type '{0}'".format(self.name))
                inject = self._server.TestPlan.check_plan_type(self.name)
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError("PlanType '{0}' not found".format(
                        self.name))
        # Initialize data from the inject and index into cache
        log.debug("Initializing PlanType ID#{0}".format(inject["id"]))
        log.xmlrpc(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["name"]
        self._index(self.name)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Type Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Clear cache, save cache level and initialize test data """
            Cache.clear()
            self.original_cache_level = get_cache_level()
            self.plantype = Nitrate()._config.plantype
            self.requests = Nitrate._requests

        def tierDown(self):
            """ Restore cache level """
            set_cache_level(self.original_cache_level)

        def test_invalid_type(self):
            """ Invalid plan type should raise exception """
            def fun():
                PlanType(name="Bad Plan Type").id
            original_log_level = get_log_level()
            set_log_level(log.CRITICAL)
            self.assertRaises(NitrateError, fun)
            set_log_level(original_log_level)

        def test_valid_type(self):
            """ Valid plan type initialization """
            # Initialize by id
            plantype = PlanType(self.plantype.id)
            self.assertEqual(plantype.name, self.plantype.name)
            # Initialize by name (explicit)
            plantype = PlanType(name=self.plantype.name)
            self.assertEqual(plantype.id, self.plantype.id)
            # Initialize by name (autodetection)
            plantype = PlanType(self.plantype.name)
            self.assertEqual(plantype.id, self.plantype.id)

        def test_cache_objects(self):
            """ Cache objects """
            set_cache_level(CACHE_OBJECTS)
            # The first round (fetch plantype data from server)
            plantype1 = PlanType(self.plantype.id)
            self.assertTrue(isinstance(plantype1.name, basestring))
            self.assertEqual(Nitrate._requests, self.requests + 1)
            # The second round (there should be no more requests)
            plantype2 = PlanType(self.plantype.id)
            self.assertTrue(isinstance(plantype2.name, basestring))
            self.assertEqual(Nitrate._requests, self.requests + 1)
            # The third round (fetching by plan type name)
            plantype3 = PlanType(self.plantype.name)
            self.assertTrue(isinstance(plantype3.id, int))
            self.assertEqual(Nitrate._requests, self.requests + 1)
            # All plan types should point to the same object
            self.assertEqual(id(plantype1), id(plantype2))
            self.assertEqual(id(plantype1), id(plantype3))

        def test_cache_none(self):
            """ Cache none """
            set_cache_level(CACHE_NONE)
            # The first round (fetch plantype data from server)
            plantype1 = PlanType(self.plantype.id)
            self.assertTrue(isinstance(plantype1.name, basestring))
            self.assertEqual(Nitrate._requests, self.requests + 1)
            # The second round (there should be another request)
            plantype2 = PlanType(self.plantype.id)
            self.assertTrue(isinstance(plantype2.name, basestring))
            self.assertEqual(Nitrate._requests, self.requests + 2)
            # The third round (fetching by plan type name)
            plantype3 = PlanType(self.plantype.name)
            self.assertTrue(isinstance(plantype3.id, int))
            self.assertEqual(Nitrate._requests, self.requests + 3)
            # Plan types should be different objects in memory
            self.assertNotEqual(id(plantype1), id(plantype2))
            self.assertNotEqual(id(plantype1), id(plantype3))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Priority Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Priority(Nitrate):
    """ Test case priority. """

    _priorities = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5']

    def __init__(self, priority):
        """
        Takes numeric priority id (1-5) or priority name which is one of:
        P1, P2, P3, P4, P5
        """

        if isinstance(priority, int):
            if priority < 1 or priority > 5:
                raise NitrateError(
                        "Not a valid Priority id: '{0}'".format(priority))
            self._id = priority
        else:
            try:
                self._id = self._priorities.index(priority)
            except ValueError:
                raise NitrateError("Invalid priority '{0}'".format(priority))

    def __unicode__(self):
        """ Return priority name for printing. """
        return self.name

    @property
    def id(self):
        """ Numeric priority id. """
        return self._id

    @property
    def name(self):
        """ Human readable priority name. """
        return self._priorities[self._id]



# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Product Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Product(Nitrate):
    """ Product. """

    # Local cache of Product
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["name"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Product id")
    name = property(_getter("name"), doc="Product name")

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # Search the cache by product name
        if "name" in kwargs:
            name = kwargs.get("name")
            return cls._cache[name], name

        return super(Product, cls)._cache_lookup(id, **kwargs)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None):
        """
        Initialize the Product by id or name

        Examples:

        Product(60)
        Product(id=60)
        Product("Red Hat Enterprise Linux 6")
        Product(name="Red Hat Enterprise Linux 6")
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id or name)
        if initialized: return
        Nitrate.__init__(self, id)

        # If inject given, fetch test case data from it
        if inject:
            self._fetch(inject)
        # Initialize by name
        elif name is not None:
            self._name = name
            self._index(name)
        # Otherwise just check that the product id was provided
        elif not id:
            raise NitrateError("Need id or name to initialize Product")

    def __unicode__(self):
        """ Product name for printing. """
        return self.name

    @staticmethod
    def search(**query):
        """ Search for products. """
        return [Product(hash["id"])
                for hash in Nitrate()._server.Product.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch product data from the server. """
        Nitrate._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.debug("Initializing Product ID#{0}".format(inject["id"]))
            log.xmlrpc(pretty(inject))
            self._id = inject["id"]
            self._name = inject["name"]
        # Search by product id
        elif self._id is not NitrateNone:
            try:
                log.info("Fetching product " + self.identifier)
                inject = self._server.Product.filter({'id': self.id})[0]
                log.debug("Initializing product " + self.identifier)
                log.xmlrpc(pretty(inject))
                self._inject = inject
                self._name = inject["name"]
            except IndexError:
                raise NitrateError(
                        "Cannot find product for " + self.identifier)
        # Search by product name
        else:
            try:
                log.info(u"Fetching product '{0}'".format(self.name))
                inject = self._server.Product.filter({'name': self.name})[0]
                log.debug(u"Initializing product '{0}'".format(self.name))
                log.xmlrpc(pretty(inject))
                self._inject = inject
                self._id = inject["id"]
            except IndexError:
                raise NitrateError(
                        "Cannot find product for '{0}'".format(self.name))
        # Index the fetched object into cache
        self._index(self.name)


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test product from the config """
            self.product = Nitrate()._config.product

        def testGetById(self):
            """ Get product by id """
            product = Product(self.product.id)
            self.assertTrue(isinstance(product, Product), "Check the instance")
            self.assertEqual(product.name, self.product.name)

        def testGetByName(self):
            """ Get product by name """
            product = Product(name=self.product.name)
            self.assertTrue(isinstance(product, Product), "Check the instance")
            self.assertEqual(product.id, self.product.id)

        def testSearch(self):
            """ Product search """
            products = Product.search(name=self.product.name)
            self.assertEqual(len(products), 1, "Single product returned")
            self.assertEqual(products[0].id, self.product.id)

        def testProductCaching(self):
            """ Test caching in Product class """
            requests = Nitrate._requests
            # Turn off caching
            set_cache_level(CACHE_NONE)
            product = Product(self.product.id)
            log.info(product.name)
            product = Product(self.product.id)
            log.info(product.name)
            self.assertEqual(Nitrate._requests, requests + 2)
            # Turn on caching
            Product._cache = {}
            set_cache_level(CACHE_OBJECTS)
            product = Product(self.product.id)
            log.info(product.name)
            product = Product(self.product.id)
            log.info(product.name)
            self.assertEqual(Nitrate._requests, requests + 3)

        def testProductAdvancedCachingID(self):
            """ Advanced caching (init by ID) """
            requests = Nitrate._requests
            Product._cache = {}
            # Turn off caching
            set_cache_level(CACHE_NONE)
            product = Product(self.product.id)
            log.info(product.name)
            product2 = Product(self.product.name)
            log.info(product2.id)
            self.assertEqual(Nitrate._requests, requests + 2)
            self.assertNotEqual(id(product), id(product2))
            # Turn on caching
            Product._cache = {}
            set_cache_level(CACHE_OBJECTS)
            product = Product(self.product.id)
            log.info(product.name)
            product2 = Product(self.product.name)
            log.info(product2.id)
            self.assertEqual(Nitrate._requests, requests + 3)
            self.assertEqual(id(product), id(product2))

        def testProductAdvancedCachingName(self):
            """ Advanced caching (init by name) """
            requests = Nitrate._requests
            Product._cache = {}
            # Turn off caching
            set_cache_level(CACHE_NONE)
            product = Product(self.product.name)
            log.info(product.id)
            product2 = Product(self.product.id)
            log.info(product2.name)
            self.assertEqual(Nitrate._requests, requests + 2)
            self.assertNotEqual(id(product), id(product2))
            # Turn on caching
            Product._cache = {}
            set_cache_level(CACHE_OBJECTS)
            product = Product(self.product.name)
            log.info(product.id)
            product2 = Product(self.product.id)
            log.info(product2.name)
            self.assertEqual(Nitrate._requests, requests + 3)
            self.assertEqual(id(product), id(product2))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Status Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanStatus(Nitrate):
    """ Test plan status (is_active field). """

    _statuses = ["DISABLED", "ENABLED"]
    _colors = ["red", "green"]

    def __init__(self, status):
        """
        Takes bool, numeric status id or status name.

        0 ... False ... DISABLED
        1 ... True .... ENABLED
        """

        if isinstance(status, int):
            if not status in [0, 1]:
                raise NitrateError(
                        "Not a valid plan status id: '{0}'".format(status))
            self._id = status
        else:
            try:
                self._id = self._statuses.index(status)
            except ValueError:
                raise NitrateError("Invalid plan status '{0}'".format(status))

    def __unicode__(self):
        """ Return plan status name for printing. """
        return self.name

    def __nonzero__(self):
        """ Boolean status representation """
        return self._id != 0

    @property
    def id(self):
        """ Numeric plan status id. """
        return self._id

    @property
    def name(self):
        """ Human readable plan status name. """
        return color(self._statuses[self.id], color=self._colors[self.id])


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Run Status Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunStatus(Nitrate):
    """ Test run status. """

    _statuses = ['RUNNING', 'FINISHED']

    def __init__(self, status):
        """
        Takes numeric status id, status name or stop date.

        A 'None' value is considered to be a 'no stop date' running:

        0 ... RUNNING  ... 'None'
        1 ... FINISHED ... '2011-07-27 15:14'
        """
        if isinstance(status, int):
            if status not in [0, 1]:
                raise NitrateError(
                        "Not a valid run status id: '{0}'".format(status))
            self._id = status
        else:
            # Running or no stop date
            if status == "RUNNING" or status == "None" or status is None:
                self._id = 0
            # Finished or some stop date
            elif status == "FINISHED" or re.match("^[-0-9: ]+$", status):
                self._id = 1
            else:
                raise NitrateError("Invalid run status '{0}'".format(status))

    def __unicode__(self):
        """ Return run status name for printing. """
        return self.name

    @property
    def id(self):
        """ Numeric runstatus id. """
        return self._id

    @property
    def name(self):
        """ Human readable runstatus name. """
        return self._statuses[self._id]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Status Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseStatus(Nitrate):
    """ Test case status. """

    _casestatuses = ['PAD', 'PROPOSED', 'CONFIRMED', 'DISABLED', 'NEED_UPDATE']

    def __init__(self, casestatus):
        """
        Takes numeric status id (1-4) or status name which is one of:
        PROPOSED, CONFIRMED, DISABLED, NEED_UPDATE
        """
        if isinstance(casestatus, int):
            if casestatus < 1 or casestatus > 4:
                raise NitrateError(
                        "Not a valid casestatus id: '{0}'".format(casestatus))
            self._id = casestatus
        else:
            try:
                self._id = self._casestatuses.index(casestatus)
            except ValueError:
                raise NitrateError(
                        "Invalid casestatus '{0}'".format(casestatus))

    def __unicode__(self):
        """ Return casestatus name for printing. """
        return self.name

    @property
    def id(self):
        """ Numeric casestatus id. """
        return self._id

    @property
    def name(self):
        """ Human readable casestatus name. """
        return self._casestatuses[self._id]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Status Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Status(Nitrate):
    """
    Test case run status.

    Used for easy converting between id and name.
    """

    _statuses = ['PAD', 'IDLE', 'PASSED', 'FAILED', 'RUNNING', 'PAUSED',
            'BLOCKED', 'ERROR', 'WAIVED']

    _colors = [None, "blue", "lightgreen", "lightred", "green", "yellow",
            "red", "magenta", "lightcyan"]

    def __init__(self, status):
        """
        Takes numeric status id (1-8) or status name which is one of:
        IDLE, PASSED, FAILED, RUNNING, PAUSED, BLOCKED, ERROR, WAIVED
        """
        if isinstance(status, int):
            if status < 1 or status > 8:
                raise NitrateError(
                        "Not a valid Status id: '{0}'".format(status))
            self._id = status
        else:
            try:
                self._id = self._statuses.index(status)
            except ValueError:
                raise NitrateError("Invalid status '{0}'".format(status))

    def __unicode__(self):
        """ Return status name for printing. """
        return self.name

    @property
    def id(self):
        """ Numeric status id. """
        return self._id

    @property
    def _name(self):
        """ Status name, plain without coloring. """
        return self._statuses[self.id]

    @property
    def name(self):
        """ Human readable status name. """
        return color(self._name, color=self._colors[self.id])

    @property
    def shortname(self):
        """ Short same-width status string (4 chars) """
        return color(self._name[0:4], color=self._colors[self.id])


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  User Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class User(Nitrate):
    """ User. """

    # Local cache of User objects indexed by user id
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["name", "login", "email"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="User id.")
    login = property(_getter("login"), doc="Login username.")
    email = property(_getter("email"), doc="User email address.")
    name = property(_getter("name"), doc="User first name and last name.")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Decorated
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # Return current user
        if id is None and 'login' not in kwargs and 'email' not in kwargs:
            return cls._cache["i-am-current-user"], "current user"
        # Search by login & email
        if "login" in kwargs:
            return cls._cache[kwargs["login"]], kwargs["login"]
        if "email" in kwargs:
            return cls._cache[kwargs["email"]], kwargs["email"]
        # Default search by id
        return super(User, cls)._cache_lookup(id, **kwargs)

    @staticmethod
    def search(**query):
        """ Search for users. """
        return [User(hash)
                for hash in Nitrate()._server.User.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, *args, **kwargs):
        """ Create a new object, handle caching if enabled """
        # Convert login or email into name for better logging
        if "login" in kwargs or "email" in kwargs:
            name = kwargs.get("login", kwargs.get("email"))
            return Nitrate.__new__(cls, id=id, name=name, *args, **kwargs)
        else:
            return Nitrate.__new__(cls, id=id, *args, **kwargs)

    def __init__(self, id=None, login=None, email=None):
        """
        Initialize by user id, login or email

        Defaults to the current user if no id, login or email provided.
        If xmlrpc initial object dict provided as the first argument,
        data are initialized directly from it.
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(
                id or login or email)
        if initialized: return
        Nitrate.__init__(self, id, prefix="UID")

        # If inject given, fetch data from it
        if inject:
            self._fetch(inject)
        # Otherwise initialize by login or email
        elif name is not None:
            if "@" in name:
                self._email = name
            else:
                self._login = name
            self._index(name)

    def __unicode__(self):
        """ User login for printing. """
        return self.name if self.name is not None else u"No Name"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch user data from the server. """
        Nitrate._fetch(self, inject)

        if inject is None:
            # Search by id
            if self._id is not NitrateNone:
                try:
                    log.info("Fetching user " + self.identifier)
                    inject = self._server.User.filter({"id": self.id})[0]
                except IndexError:
                    raise NitrateError(
                            "Cannot find user for " + self.identifier)
            # Search by login
            elif self._login is not NitrateNone:
                try:
                    log.info(
                            "Fetching user for login '{0}'".format(self.login))
                    inject = self._server.User.filter(
                            {"username": self.login})[0]
                except IndexError:
                    raise NitrateError("No user found for login '{0}'".format(
                            self.login))
            # Search by email
            elif self._email is not NitrateNone:
                try:
                    log.info("Fetching user for email '{0}'".format(
                            self.email))
                    inject = self._server.User.filter({"email": self.email})[0]
                except IndexError:
                    raise NitrateError("No user found for email '{0}'".format(
                            self.email))
            # Otherwise initialize to the current user
            else:
                log.info("Fetching the current user")
                inject = self._server.User.get_me()
                self._index("i-am-current-user")

        # Initialize data from the inject and index into cache
        log.debug("Initializing user UID#{0}".format(inject["id"]))
        log.xmlrpc(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._login = inject["username"]
        self._email = inject["email"]
        if inject["first_name"] and inject["last_name"]:
            self._name = inject["first_name"] + " " + inject["last_name"]
        else:
            self._name = None
        self._index(self.login, self.email)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Clear cache, save cache level and initialize test data """
            Cache.clear()
            self.original_cache_level = get_cache_level()
            self.user = Nitrate()._config.user
            self.requests = Nitrate._requests

        def tierDown(self):
            """ Restore cache level """
            set_cache_level(self.original_cache_level)

        def test_no_name(self):
            """ User with no name set in preferences """
            user = User()
            user._name = None
            self.assertEqual(unicode(user), u"No Name")
            self.assertEqual(str(user), "No Name")

        def test_current_user(self):
            """ Current user available & sane """
            user = User()
            for data in [user.login, user.email, user.name]:
                self.assertTrue(isinstance(data, basestring))
            self.assertTrue(isinstance(user.id, int))

        def test_cache_none(self):
            """ Cache none """
            set_cache_level(CACHE_NONE)
            # Initialize the same user by id, login and email
            user1 = User(self.user.id)
            log.info(user1.name)
            user2 = User(self.user.login)
            log.info(user2.name)
            user3 = User(self.user.email)
            log.info(user3.name)
            # Three requests to the server should be performed
            self.assertEqual(Nitrate._requests, self.requests + 3)
            # User data should be the same
            for user in [user1, user2, user3]:
                self.assertEqual(user.id, self.user.id)
                self.assertEqual(user.login, self.user.login)
                self.assertEqual(user.email, self.user.email)
            # Users should be different objects in memory
            self.assertNotEqual(id(user1), id(user2))
            self.assertNotEqual(id(user1), id(user3))

        def test_cache_objects(self):
            """ Cache objects """
            set_cache_level(CACHE_OBJECTS)
            # Initialize the same user by id, login and email
            user1 = User(self.user.id)
            log.info(user1.name)
            user2 = User(self.user.login)
            log.info(user2.name)
            user3 = User(self.user.email)
            log.info(user3.name)
            # Single request to the server should be performed
            self.assertEqual(Nitrate._requests, self.requests + 1)
            # All users objects should be identical
            self.assertEqual(id(user1), id(user2))
            self.assertEqual(id(user1), id(user3))

        def test_initialization_by_id(self):
            """ Initializate by id """
            user = User(self.user.id)
            self.assertEqual(user.id, self.user.id)
            self.assertEqual(user.login, self.user.login)
            self.assertEqual(user.email, self.user.email)

        def test_initialization_by_login(self):
            """ Initializate by login """
            # Check both explicit parameter and autodetection
            user1 = User(login=self.user.login)
            user2 = User(self.user.login)
            for user in [user1, user2]:
                self.assertEqual(user.id, self.user.id)
                self.assertEqual(user.login, self.user.login)
                self.assertEqual(user.email, self.user.email)

        def test_initialization_by_email(self):
            """ Initializate by email """
            # Check both explicit parameter and autodetection
            user1 = User(email=self.user.email)
            user2 = User(self.user.email)
            for user in [user1, user2]:
                self.assertEqual(user.id, self.user.id)
                self.assertEqual(user.login, self.user.login)
                self.assertEqual(user.email, self.user.email)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Version Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Version(Nitrate):
    """ Product version. """

    # Local cache of Version
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["name", "product"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Version id")
    name = property(_getter("name"), doc="Version name")
    product = property(_getter("product"), doc="Version product")

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """

        # Search cache by the version name and product
        if "product" in kwargs and ("version" in kwargs or "name" in kwargs):
            product = kwargs.get("product")
            if isinstance(product, Product):
                product = product.name
            name = kwargs.get("name", kwargs.get("version"))
            return cls._cache["{0}---in---{1}".format(name, product)], name

        # Default search by id otherwise
        return super(Version, cls)._cache_lookup(id, **kwargs)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None, product=None, **kwargs):
        """ Initialize by version id or product and version. """

        # Backward compatibility for 'version' argument (now called 'name')
        name = name if name is not None else kwargs.get("version")

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id)
        if initialized: return
        Nitrate.__init__(self, id)

        # If inject given, fetch tag data from it
        if inject:
            self._fetch(inject)
        # Initialize by version name and product
        elif name is not None and product is not None:
            self._name = name
            # Convert product into object if necessary
            if isinstance(product, Product):
                self._product = product
            else:
                self._product = Product(product)
            # Index by name/product (but only when the product name is known)
            if self.product._name is not NitrateNone:
                self._index("{0}---in---{1}".format(
                        self.name, self.product.name))
        # Otherwise just make sure the version id was provided
        elif not id:
            raise NitrateError("Need either version id or both product "
                    "and version name to initialize the Version object.")

    def __unicode__(self):
        """ Version name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch version data from the server. """
        Nitrate._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.debug("Processing Version ID#{0} inject".format(inject["id"]))
        # Search by version id
        elif self._id is not NitrateNone:
            try:
                log.info("Fetching version {0}".format(self.identifier))
                inject = self._server.Product.filter_versions(
                        {'id': self.id})[0]
            except IndexError:
                raise NitrateError(
                        "Cannot find version for {0}".format(self.identifier))
        # Search by product and name
        else:
            try:
                log.info(u"Fetching version '{0}' of '{1}'".format(
                        self.name, self.product.name))
                inject = self._server.Product.filter_versions(
                        {'product': self.product.id, 'value': self.name})[0]
            except IndexError:
                raise NitrateError(
                        "Cannot find version for '{0}'".format(self.name))
        # Initialize data from the inject and index into cache
        log.debug("Initializing Version ID#{0}".format(inject["id"]))
        log.xmlrpc(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["value"]
        self._product = Product(inject["product_id"])
        # Index by product name & version name (if product is cached)
        if self.product._name is not NitrateNone:
            self._index("{0}---in---{1}".format(self.name, self.product.name))
        # Otherwise index by id only
        else:
            self._index()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up version from the config """
            Cache.clear()
            self.cache_level = get_cache_level()
            self.version = Nitrate()._config.version
            self.product = Nitrate()._config.product
            self.requests = Nitrate._requests

        def tierDown(self):
            """ Restore cache level """
            set_cache_level(self.cache_level)

        def test_fetch_by_id(self):
            """ Fetch by id """
            version = Version(self.version.id)
            self.assertEqual(version.name, self.version.name)

        def test_fetch_by_name_and_product(self):
            """ Fetch by name and product """
            # Named arguments
            version = Version(
                    name=self.version.name, product=self.product.name)
            self.assertEqual(version.id, self.version.id)
            # Backward compatibility
            version = Version(
                    version=self.version.name, product=self.product.name)
            self.assertEqual(version.id, self.version.id)

        def test_cache_none(self):
            """ Cache none """
            set_cache_level(CACHE_NONE)
            version = Version(self.version.id)
            self.assertEqual(version.name, self.version.name)
            version = Version(self.version.id)
            self.assertEqual(version.name, self.version.name)
            # Fetches the version twice ---> 2 requests
            self.assertEqual(Nitrate._requests, self.requests + 2)

        def test_cache_objects(self):
            """ Cache objects """
            set_cache_level(CACHE_OBJECTS)
            version = Version(self.version.id)
            self.assertEqual(version.name, self.version.name)
            version = Version(self.version.id)
            self.assertEqual(version.name, self.version.name)
            # Should fetch version just once ---> 1 request
            self.assertEqual(Nitrate._requests, self.requests + 1)

        def test_cache_persistent(self):
            """ Cache persistent """
            set_cache_level(CACHE_PERSISTENT)
            # Fetch the version (populate the cache)
            version = Version(self.version.id)
            self.assertEqual(version.name, self.version.name)
            # Save, clear & load cache
            Cache.save()
            Cache.clear()
            Cache.load()
            requests = Nitrate._requests
            # Fetch once again ---> no additional request
            version = Version(self.version.id)
            self.assertEqual(version.name, self.version.name)
            self.assertEqual(Nitrate._requests, requests)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Mutable Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Mutable(Nitrate):
    """
    General class for all mutable Nitrate objects.

    Provides the update() method which pushes the changes (if any
    happened) to the Nitrate server and the _update() method performing
    the actual update (to be implemented by respective class).
    """

    # Default expiration for mutable objects is 1 hour
    _expiration = datetime.timedelta(hours=1)

    def __init__(self, id=None, prefix="ID"):
        """ Initially set up to unmodified state. """
        self._modified = False
        Nitrate.__init__(self, id, prefix)

    def _update(self):
        """ Save data to server (to be implemented by respective class) """
        raise NitrateError("Data update not implemented")

    def update(self):
        """ Update the data, if modified, to the server """
        if self._modified:
            self._update()
            self._modified = False
            # Data are now in sync with the server
            self._fetched = datetime.datetime.now()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Container Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Container(Mutable):
    """
    General container class for handling sets of objects.

    Provides the add() and remove() methods for adding and removing
    objects and the internal _add() and _remove() which perform the
    actual update to the server (implemented by respective class).

    Container overview (objects contained are listed in brackets):

    TestPlan.tags = PlanTags[Tag] ......................... done
    TestPlan.components = PlanComponents[Component] ....... done
    TestPlan.children = ChildPlans[TestPlan] .............. done
    TestPlan.testcases = PlanCases[TestCase] .............. done
    TestPlan.testruns = PlanRuns[TestRun] ................. done
    TestPlan.caseplans = PlanCasePlans[CasePlan] .......... implement

    TestRun.tags = RunTags[Tag] ........................... done
    TestRun.caseruns = RunCaseRuns[CaseRun] ............... done
    TestRun.testcases = RunCases[TestCase] ................ done

    TestCase.tags = CaseTags[Tag] ......................... done
    TestCase.components = CaseComponents[Component] ....... done
    TestCase.testplans = CasePlans[TestPlan] .............. done
    TestCase.testruns = CaseRuns[TestRun] ................. needed?
    TestCase.caseruns = CaseCaseRuns[CaseRun] ............. needed?
    TestCase.caseplans = CaseCasePlans[CasePlan] .......... needed?
    TestCase.bugs = CaseBugs[Bug] ......................... done

    CaseRun.bugs = CaseRunBugs[Bug] ....................... done
    """

    # List of all object attributes (used for init & expiration)
    _attributes = ["current", "original"]

    # Class of objects to be contained (defined in each container)
    _class = None

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Related object id.")

    @property
    def _items(self):
        """ Set representation containing the items. """
        if self._current is NitrateNone:
            self._fetch()
        # Fetch the whole container if there are some uncached items
        if not self._class._is_cached(self._current):
            self._fetch()
        return self._current

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, object, inset=None):
        """ Create new container objects based on the object id """
        return super(Container, cls).__new__(cls, object.id)

    def __init__(self, object, inset=None):
        """ Initialize container for specified object. """
        # Initialize (unless already done)
        if self._id is not None:
            # Initialized but not fetched ---> fetch from the inset if given
            if inset is not None and not self._is_cached(self):
                self._fetch(inset)
            return
        Mutable.__init__(self, object.id)
        self._identifier = object.identifier
        self._object = object
        # Initialize directly if initial set provided
        if inset is not None:
            self._fetch(inset)

    def __iter__(self):
        """ Container iterator. """
        for item in self._items:
            yield item

    def __contains__(self, item):
        """ Container 'in' operator. """
        return item in self._items

    def __len__(self):
        """ Number of container items. """
        return len(self._items)

    def __unicode__(self):
        """ Display items as a list for printing. """
        if self._items:
            # List of identifiers
            try:
                return listed(sorted(
                    [item.identifier for item in self._items]))
            # If no identifiers, just join strings
            except AttributeError:
                return listed(self._items, quote="'")
        else:
            return "[None]"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Save cache timestamp and initialize from inset if given """
        Nitrate._fetch(self)
        # Create copies of the initial set (if given)
        if inset is not None:
            log.debug("Initializing {0} for {1} from the inset".format(
                    self.__class__.__name__, self._identifier))
            log.debug(pretty(inset))
            self._current = set(inset)
            self._original = set(inset)
        # Cache into container class
        if get_cache_level() >= CACHE_OBJECTS:
            self.__class__._cache[self._id] = self
        # Return True if the data are already initialized
        return inset is not None

    def add(self, items):
        """ Add an item or a list of items to the container. """

        # Convert to set representation
        if isinstance(items, list):
            items = set(items)
        else:
            items = set([items])

        # If there are any new items
        add_items = items - self._items
        if add_items:
            log.info("Adding {0} to {1}'s {2}".format(
                    listed([item.identifier for item in add_items],
                        self._class.__name__, max=10),
                    self._object.identifier,
                    self.__class__.__name__))
            self._items.update(items)
            if _cache_level != CACHE_NONE:
                self._modified = True
            else:
                self._update()

    def remove(self, items):
        """ Remove an item or a list of items from the container. """

        # Convert to set representation
        if isinstance(items, list):
            items = set(items)
        else:
            items = set([items])

        # If there are any items to be removed
        remove_items = items.intersection(self._items)
        if remove_items:
            log.info("Removing {0} from {1}'s {2}".format(
                    listed([item.identifier for item in remove_items],
                        self._class.__name__, max=10),
                    self._object.identifier,
                    self.__class__.__name__))
            self._items.difference_update(items)
            if _cache_level != CACHE_NONE:
                self._modified = True
            else:
                self._update()

    def clear(self):
        """ Remove all items from the container. """
        self.remove(list(self._items))

    def _add(self, items):
        """ Add provided items to the server. """
        raise NitrateError("To be implemented by respective class.")

    def _remove(self, items):
        """ Remove provided items from the server. """
        raise NitrateError("To be implemented by respective class.")

    def _update(self):
        """ Update container changes to the server. """
        # Added items
        added = self._current - self._original
        if added: self._add(added)

        # Removed items
        removed = self._original - self._current
        if removed: self._remove(removed)

        # Save the current state as the original (for future updates)
        self._original = set(self._current)

    def _sleep(self):
        """ Prepare container items for caching """
        # When restoring the container from the cache, unpickling failed
        # because of trying to construct set() of objects which were not
        # fully rebuild yet (__hash__ failed because of missing self._id).
        # So we need to convert containers into list of ids before the
        # cache dump and instantiate the objects back after cache restore.
        if self._current is NitrateNone: return
        self._original = [item.id for item in self._original]
        self._current = [item.id for item in self._current]

    def _wake(self):
        """ Restore container object after loading from cache """
        # See _sleep() method above for explanation why this is necessary
        if self._current is NitrateNone: return
        log.cache("Waking up {0} for {1}".format(
                self.__class__.__name__, self._identifier))
        self._original = set([self._class(id) for id in self._original])
        self._current = set([self._class(id) for id in self._current])


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Component Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Component(Nitrate):
    """ Test case component. """

    # Local cache of Component objects indexed by component id plus
    # additionaly by name-in-product pairs
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["name", "product"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Component Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Component id.")
    name = property(_getter("name"), doc="Component name.")
    product = property(_getter("product"), doc="Relevant product.")

    @property
    def synopsis(self):
        """ Short component summary (including product info). """
        return "{0}, {1}".format(self.name, self.product)

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """

        # Name and product check
        if 'product' in kwargs and 'name' in kwargs:
            product = kwargs.get("product")
            if isinstance(product, Product):
                product = product.name
            name = kwargs.get("name")
            return cls._cache["{0}---in---{1}".format(name, product)], name

        return super(Component, cls)._cache_lookup(id, **kwargs)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Component Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None, product=None, **kwargs):
        """ Initialize by component id or component name and product """

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id)
        if initialized: return
        Nitrate.__init__(self, id)

        # If inject given, fetch component data from it
        if inject:
            self._fetch(inject)
        # Initialized by product and component name
        elif name is not None and product is not None:
            # Detect product format
            if isinstance(product, Product):
                self._product = product
            else:
                self._product = Product(product)
            self._name = name
            # Index by name-product (only when the product name is known)
            if self.product._name is not NitrateNone:
                self._index("{0}---in---{1}".format(
                        self.name, self.product.name))
        # Otherwise just check that the id was provided
        elif id is None:
            raise NitrateError("Need either component id or both product "
                    "and component name to initialize the Component object.")

    def __unicode__(self):
        """ Component name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Component Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing component data """
        Nitrate._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing component ID#{0} inject".format(inject["id"]))
        # Search by component id
        elif self._id is not NitrateNone:
            try:
                log.info("Fetching component " + self.identifier)
                inject = self._server.Product.get_component(self.id)
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError(
                        "Cannot find component for " + self.identifier)
        # Search by component name and product
        else:
            try:
                log.info(u"Fetching component '{0}' of '{1}'".format(
                        self.name, self.product.name))
                inject = self._server.Product.check_component(
                        self.name, self.product.id)
            except xmlrpclib.Fault, error:
                log.error(error)
                raise NitrateError("Component '{0}' not found in"
                        " '{1}'".format(self.name, self.product.name))

        # Initialize data from the inject and index into cache
        log.debug("Initializing component ID#{0}".format(inject["id"]))
        log.xmlrpc(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["name"]
        self._product = Product(
                {"id": inject["product_id"], "name": inject["product"]})
        self._index("{0}---in---{1}".format(self.name, self.product.name))

    @staticmethod
    def search(**query):
        """ Search for components. """
        return [Component(hash) for hash in
                Nitrate()._server.Product.filter_components(dict(query))]


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Component Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up component from the config """
            self.component = Nitrate()._config.component

        def testFetchById(self):
            """ Fetch component by id """
            component = Component(self.component.id)
            self.assertTrue(isinstance(component, Component))
            self.assertEqual(component.name, self.component.name)
            self.assertEqual(component.product.name, self.component.product)

        def testFetchByName(self):
            """ Fetch component by name and product """
            component = Component(
                    name=self.component.name, product=self.component.product)
            self.assertTrue(isinstance(component, Component))
            self.assertEqual(component.id, self.component.id)

        def testSearchByName(self):
            """ Search for component by name """
            components = Component.search(name=self.component.name)
            self.assertTrue(components[0].name == self.component.name)

        def testCachingOn(self):
            """ Component caching on """
            # Make sure the cache is empty
            Component._cache = {}
            # Enable cache, remember current number of requests
            original = get_cache_level()
            set_cache_level(CACHE_OBJECTS)
            requests = Nitrate._requests
            # The first round (fetch component data from server)
            component = Component(self.component.id)
            self.assertTrue(isinstance(component.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            # The second round (there should be no more requests)
            component = Component(self.component.id)
            self.assertTrue(isinstance(component.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            # Restore cache level
            set_cache_level(original)

        def testCachingOff(self):
            """ Component caching off """
            # Enable cache, remember current number of requests
            original = get_cache_level()
            set_cache_level(CACHE_NONE)
            requests = Nitrate._requests
            # The first round (fetch component data from server)
            component = Component(self.component.id)
            self.assertTrue(isinstance(component.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            del component
            # The second round (there should be another request)
            component = Component(self.component.id)
            self.assertTrue(isinstance(component.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 2)
            # Restore cache level
            set_cache_level(original)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   Case Components Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseComponents(Container):
    """ Components linked to a test case. """

    # Local cache indexed by corresponding test case id
    _cache = {}
    # Class of contained objects
    _class = Component

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Components Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __unicode__(self):
        """ The list of linked components' names """
        if self._items:
            return listed(sorted([component.name for component in self]))
        else:
            return "[None]"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Components Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Fetch currently linked components from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s components".format(self._identifier))
        self._current = set([Component(inject)
                for inject in self._server.TestCase.get_components(self.id)])
        self._original = set(self._current)

    def _add(self, components):
        """ Link provided components to the test case. """
        log.info(u"Linking {1} to {0}".format(self._identifier,
                    listed([component.name for component in components])))
        data = [component.id for component in components]
        log.xmlrpc(data)
        self._server.TestCase.add_component(self.id, data)

    def _remove(self, components):
        """ Unlink provided components from the test case. """
        for component in components:
            log.info(u"Unlinking {0} from {1}".format(
                    component.name, self._identifier))
            self._server.TestCase.remove_component(self.id, component.id)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Components Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up component from the config """
            self.component = Nitrate()._config.component
            self.testcase = Nitrate()._config.testcase

        def test1(self):
            """ Unlinking a component from a test case """
            testcase = TestCase(self.testcase.id)
            component = Component(self.component.id)
            testcase.components.remove(component)
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component not in testcase.components)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component not in testcase.components)

        def test2(self):
            """ Linking a component to a test case """
            testcase = TestCase(self.testcase.id)
            component = Component(self.component.id)
            testcase.components.add(component)
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component in testcase.components)
            # Check server content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component in testcase.components)

        def test3(self):
            """ Unlinking a component from a test case """
            testcase = TestCase(self.testcase.id)
            component = Component(self.component.id)
            testcase.components.remove(component)
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component not in testcase.components)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component not in testcase.components)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#   Plan Components Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanComponents(Container):
    """ Components linked to a test plan """

    # Local cache indexed by corresponding test plan id
    _cache = {}
    # Class of contained objects
    _class = Component

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Components Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __unicode__(self):
        """ The list of linked components' names """
        if self._items:
            return listed(sorted([component.name for component in self]))
        else:
            return "[None]"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Components Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Fetch currently linked components from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s components".format(self._identifier))
        self._current = set([Component(inject)
                for inject in self._server.TestPlan.get_components(self.id)])
        self._original = set(self._current)

    def _add(self, components):
        """ Link provided components to the test plan """
        log.info(u"Linking {1} to {0}".format(self._identifier,
                    listed([component.name for component in components])))
        data = [component.id for component in components]
        log.xmlrpc(data)
        self._server.TestPlan.add_component(self.id, data)

    def _remove(self, components):
        """ Unlink provided components from the test plan """
        for component in components:
            log.info(u"Unlinking {0} from {1}".format(
                    component.name, self._identifier))
            self._server.TestPlan.remove_component(self.id, component.id)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Components Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up component from the config """
            self.component = Nitrate()._config.component
            self.testplan = Nitrate()._config.testplan

        def test1(self):
            """ Unlinking a component from a  test plan """
            testplan = TestPlan(self.testplan.id)
            component = Component(self.component.id)
            testplan.components.remove(component)
            testplan.update()
            # Check cache content
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(component not in testplan.components)
            # Check server content
            Cache.clear()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(component not in testplan.components)

        def test2(self):
            """ Linking a component to a  test plan """
            testplan = TestPlan(self.testplan.id)
            component = Component(self.component.id)
            testplan.components.add(component)
            testplan.update()
            # Check cache content
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(component in testplan.components)
            # Check server content
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(component in testplan.components)

        def test3(self):
            """ Unlinking a component from a  test plan """
            testplan = TestPlan(self.testplan.id)
            component = Component(self.component.id)
            testplan.components.remove(component)
            testplan.update()
            # Check cache content
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(component not in testplan.components)
            # Check server content
            Cache.clear()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(component not in testplan.components)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Bug Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Bug(Nitrate):
    """ Bug related to a test case or a case run. """

    # Local cache of Bug objects indexed by internal bug id
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["bug", "system", "testcase", "caserun"]

    # Prefixes for bug systems, identifier width
    _prefixes = {1: "BZ"}
    _identifier_width = 7

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bug Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Bug id (internal).")
    bug = property(_getter("bug"), doc="Bug (external id).")
    system = property(_getter("system"), doc="Bug system.")
    testcase = property(_getter("testcase"), doc="Test case.")
    caserun = property(_getter("caserun"), doc="Case run.")

    @property
    def synopsis(self):
        """ Short summary about the bug """
        # Summary in the form: BUG#123456 (BZ#123, TC#456, CR#789)
        return "{0} ({1})".format(self.identifier, ", ".join([str(self)] +
                [obj.identifier for obj in (self.testcase, self.caserun)
                if obj is not None]))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bug Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, bug=None, system=1, **kwargs):
        """
        Initialize the bug

        Provide external bug id, optionally bug system (Bugzilla by default).
        """

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id)
        if initialized: return
        Nitrate.__init__(self, id, prefix="BUG")

        # If inject given, fetch bug data from it
        if inject:
            self._fetch(inject)
        # Initialized by bug id and system id
        elif bug is not None and system is not None:
            self._bug = bug
            self._system = system
        # Otherwise just check that the id was provided
        elif id is None:
            raise NitrateError("Need bug id to initialize the Bug object.")

    def __eq__(self, other):
        """
        Custom bug comparison

        Primarily decided by id. If unknown, compares by bug id & bug system.
        """
        # Decide by internal id
        if self._id is not NitrateNone and other._id is not NitrateNone:
            return self.id == other.id
        # Compare external id and bug system id
        return self.bug == other.bug and self.system == other.system

    def __unicode__(self):
        """ Bug name for printing. """
        try:
            prefix = self._prefixes[self.system]
        except KeyError:
            prefix = "BZ"
        return u"{0}#{1}".format(prefix, str(self.bug).rjust(
                self._identifier_width, "0"))

    def __hash__(self):
        """ Construct the uniqe hash from bug id and bug system id """
        return _idify([self.system, self.bug])

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bug Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch bug info from the server """
        Nitrate._fetch(self, inject)
        # No direct xmlrpc function for fetching so far
        if inject is None:
            raise NotImplementedError("Direct bug fetching not implemented")
        # Process provided inject
        self._id = int(inject["id"])
        self._bug = int(inject["bug_id"])
        self._system = int(inject["bug_system_id"])
        self._testcase = TestCase(int(inject["case_id"]))
        if inject["case_run_id"] is not None:
            self._caserun = CaseRun(int(inject["case_run_id"]))
        # Index the fetched object into cache
        self._index()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Bugs Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseBugs(Container):
    """ Bugs attached to a test case """

    # Local cache of bugs attached to a test case
    _cache = {}

    # Class of contained objects
    _class = Bug

    def _fetch(self, inset=None):
        """ Fetch currently attached bugs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching bugs for {0}".format(self._identifier))
        injects = self._server.TestCase.get_bugs(self.id)
        log.xmlrpc(pretty(injects))
        self._current = set([Bug(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, bugs):
        """ Attach provided bugs to the test case """
        log.info(u"Attaching {0} to {1}".format(
                listed(bugs), self._identifier))
        data = [{
                "bug_id": bug.bug,
                "bug_system_id": bug.system,
                "case_id": self.id} for bug in bugs]
        log.xmlrpc(pretty(data))
        self._server.TestCase.attach_bug(data)
        # Fetch again the whole bug list (to get the internal id)
        self._fetch()

    def _remove(self, bugs):
        """ Detach provided bugs from the test case """
        log.info(u"Detaching {0} from {1}".format(
                listed(bugs), self._identifier))
        data = [bug.bug for bug in bugs]
        log.xmlrpc(pretty(data))
        self._server.TestCase.detach_bug(self.id, data)

    # Print unicode list of bugs
    def __unicode__(self):
        return listed(self._items)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Bugs Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test case from the config """
            self.testcase = Nitrate()._config.testcase
            self.bug = Bug(bug=1234)

        def test_bugging1(self):
            """ Detaching bug from a test case """
            # Detach bug and check
            testcase = TestCase(self.testcase.id)
            testcase.bugs.remove(self.bug)
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(self.bug not in testcase.bugs)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(self.bug not in testcase.bugs)

        def test_bugging2(self):
            """ Attaching bug to a test case """
            # Attach bug and check
            testcase = TestCase(self.testcase.id)
            testcase.bugs.add(self.bug)
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(self.bug in testcase.bugs)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(self.bug in testcase.bugs)

        def test_bugging3(self):
            """ Detaching bug from a test case """
            # Detach bug and check
            testcase = TestCase(self.testcase.id)
            testcase.bugs.remove(self.bug)
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(self.bug not in testcase.bugs)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(self.bug not in testcase.bugs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Run Bugs Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseRunBugs(Container):
    """ Bugs attached to a test case run """

    # Local cache of bugs attached to a test case
    _cache = {}

    # Class of contained objects
    _class = Bug

    def _fetch(self, inset=None):
        """ Fetch currently attached bugs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching bugs for {0}".format(self._identifier))
        injects = self._server.TestCaseRun.get_bugs(self.id)
        log.xmlrpc(pretty(injects))
        self._current = set([Bug(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, bugs):
        """ Attach provided bugs to the test case """
        log.info(u"Attaching {0} to {1}".format(
                listed(bugs), self._identifier))
        data = [{
                "bug_id": bug.bug,
                "bug_system_id": bug.system,
                "case_run_id": self.id} for bug in bugs]
        log.xmlrpc(pretty(data))
        self._server.TestCaseRun.attach_bug(data)
        # Fetch again the whole bug list (to get the internal id)
        self._fetch()

    def _remove(self, bugs):
        """ Detach provided bugs from the test case """
        log.info(u"Detaching {0} from {1}".format(
                listed(bugs), self._identifier))
        data = [bug.bug for bug in bugs]
        log.xmlrpc(pretty(data))
        self._server.TestCaseRun.detach_bug(self.id, data)

    # Print unicode list of bugs
    def __unicode__(self):
        return listed(self._items)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Run Bugs Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test case from the config """
            self.caserun = Nitrate()._config.caserun
            self.bug = Bug(bug=1234)

        def test_bugging1(self):
            """ Detaching bug from a test case run """
            # Detach bug and check
            caserun = CaseRun(self.caserun.id)
            caserun.bugs.remove(self.bug)
            caserun.update()
            # Check cache content
            caserun = CaseRun(self.caserun.id)
            self.assertTrue(self.bug not in caserun.bugs)
            # Check server content
            Cache.clear()
            caserun = CaseRun(self.caserun.id)
            self.assertTrue(self.bug not in caserun.bugs)

        def test_bugging2(self):
            """ Attaching bug to a test case run """
            # Attach bug and check
            caserun = CaseRun(self.caserun.id)
            caserun.bugs.add(self.bug)
            caserun.update()
            # Check cache content
            caserun = CaseRun(self.caserun.id)
            self.assertTrue(self.bug in caserun.bugs)
            # Check server content
            Cache.clear()
            caserun = CaseRun(self.caserun.id)
            self.assertTrue(self.bug in caserun.bugs)

        def test_bugging3(self):
            """ Detaching bug from a test case run """
            # Detach bug and check
            caserun = CaseRun(self.caserun.id)
            caserun.bugs.remove(self.bug)
            caserun.update()
            # Check cache content
            caserun = CaseRun(self.caserun.id)
            self.assertTrue(self.bug not in caserun.bugs)
            # Check server content
            Cache.clear()
            caserun = CaseRun(self.caserun.id)
            self.assertTrue(self.bug not in caserun.bugs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Tag Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Tag(Nitrate):
    """ Tag Class """

    # List of all object attributes (used for init & expiration)
    _attributes = ["name"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Tag Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Tag id")
    name = property(_getter("name"), doc="Tag name")

    # Local cache for Tag
    _cache = {}

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Tag Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None):
        """ Initialize by tag id or tag name """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id or name)
        if initialized: return
        Nitrate.__init__(self, id)

        # If inject given, fetch tag data from it
        if inject:
            self._fetch(inject)
        # Initialize by name
        elif name is not None:
            self._name = name
            self._index(name)
        # Otherwise just check that the tag name or id was provided
        elif not id:
            raise NitrateError("Need either tag id or tag name "
                    "to initialize the Tag object.")

    def __unicode__(self):
        """ Tag name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Tag Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch tag data from the server. """
        Nitrate._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.debug("Initializing Tag ID#{0}".format(inject["id"]))
            log.xmlrpc(pretty(inject))
            self._id = inject["id"]
            self._name = inject["name"]
        # Search by tag id
        elif self._id is not NitrateNone:
            try:
                log.info("Fetching tag " + self.identifier)
                inject = self._server.Tag.get_tags({'ids': [self.id]})
                log.debug("Initializing tag " + self.identifier)
                log.xmlrpc(pretty(inject))
                self._inject = inject
                self._name = inject[0]["name"]
            except IndexError:
                raise NitrateError(
                        "Cannot find tag for {0}".format(self.identifier))
        # Search by tag name
        else:
            try:
                log.info(u"Fetching tag '{0}'".format(self.name))
                inject = self._server.Tag.get_tags({'names': [self.name]})
                log.debug(u"Initializing tag '{0}'".format(self.name))
                log.xmlrpc(pretty(inject))
                self._inject = inject
                self._id = inject[0]["id"]
            except IndexError:
                raise NitrateError(
                        "Cannot find tag '{0}'".format(self.name))
        # Index the fetched object into cache
        self._index(self.name)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanTags(Container):
    """ Test plan tags. """

    _cache = {}

    # Class of contained objects
    _class = Tag

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server. """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching tags for {0}".format(self._identifier))
        injects = self._server.TestPlan.get_tags(self.id)
        log.debug(pretty(injects))
        self._current = set([Tag(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test plan. """
        log.info(u"Tagging {0} with {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestPlan.add_tag(self.id, list(tag.name for tag in tags))

    def _remove(self, tags):
        """ Detach provided tags from the test plan. """
        log.info(u"Untagging {0} of {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestPlan.remove_tag(self.id, list(
                tag.name for tag in tags))

    # Print unicode list of tags
    def __unicode__(self):
        return listed(self._items, quote="'")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Plan Tags Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan

        def testTagging1(self):
            """ Untagging a test plan """
            # Remove tag and check
            testplan = TestPlan(self.testplan.id)
            testplan.tags.remove(Tag("TestTag"))
            testplan.update()
            # Check cache content
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(Tag("TestTag") not in testplan.tags)
            # Check server content
            Cache.clear()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(Tag("TestTag") not in testplan.tags)

        def testTagging2(self):
            """ Tagging a test plan """
            # Add tag and check
            testplan = TestPlan(self.testplan.id)
            testplan.tags.add(Tag("TestTag"))
            testplan.update()
            # Check cache content
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(Tag("TestTag") in testplan.tags)
            # Check server content
            Cache.clear()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(Tag("TestTag") in testplan.tags)

        def testTagging3(self):
            """ Untagging a test plan """
            # Remove tag and check
            testplan = TestPlan(self.testplan.id)
            testplan.tags.remove(Tag("TestTag"))
            testplan.update()
            # Check cache content
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(Tag("TestTag") not in testplan.tags)
            # Check server content
            Cache.clear()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(Tag("TestTag") not in testplan.tags)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Run Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunTags(Container):
    """ Test run tags. """

    _cache = {}

    # Class of contained objects
    _class = Tag

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching tags for {0}".format(self._identifier))
        injects = self._server.TestRun.get_tags(self.id)
        log.debug(pretty(injects))
        self._current = set([Tag(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test run. """
        log.info(u"Tagging {0} with {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestRun.add_tag(self.id, list(tag.name for tag in tags))

    def _remove(self, tags):
        """ Detach provided tags from the test run. """
        log.info(u"Untagging {0} of {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestRun.remove_tag(self.id, list(
                tag.name for tag in tags))

    # Print unicode list of tags
    def __unicode__(self):
        return listed(self._items, quote="'")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Run Tags Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test run from the config """
            self.testrun = Nitrate()._config.testrun

        def testTagging1(self):
            """ Untagging a test run """
            # Remove tag and check
            testrun = TestRun(self.testrun.id)
            testrun.tags.remove(Tag("TestTag"))
            testrun.update()
            # Check cache content
            testrun = TestRun(self.testrun.id)
            self.assertTrue(Tag("TestTag") not in testrun.tags)
            # Check server content
            Cache.clear()
            testrun = TestRun(self.testrun.id)
            self.assertTrue(Tag("TestTag") not in testrun.tags)

        def testTagging2(self):
            """ Tagging a test run """
            # Add tag and check
            testrun = TestRun(self.testrun.id)
            testrun.tags.add(Tag("TestTag"))
            testrun.update()
            # Check cache content
            testrun = TestRun(self.testrun.id)
            self.assertTrue(Tag("TestTag") in testrun.tags)
            # Check server content
            Cache.clear()
            testrun = TestRun(self.testrun.id)
            self.assertTrue(Tag("TestTag") in testrun.tags)

        def testTagging3(self):
            """ Untagging a test run """
            # Remove tag and check
            testrun = TestRun(self.testrun.id)
            testrun.tags.remove(Tag("TestTag"))
            testrun.update()
            # Check cache content
            testrun = TestRun(self.testrun.id)
            self.assertTrue(Tag("TestTag") not in testrun.tags)
            # Check server content
            Cache.clear()
            testrun = TestRun(self.testrun.id)
            self.assertTrue(Tag("TestTag") not in testrun.tags)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseTags(Container):
    """ Test case tags. """

    _cache = {}

    # Class of contained objects
    _class = Tag

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching tags for {0}".format(self._identifier))
        injects = self._server.TestCase.get_tags(self.id)
        log.debug(pretty(injects))
        self._current = set([Tag(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test case. """
        log.info(u"Tagging {0} with {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestCase.add_tag(self.id, list(tag.name for tag in tags))

    def _remove(self, tags):
        """ Detach provided tags from the test case. """
        log.info(u"Untagging {0} of {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestCase.remove_tag(self.id, list(
                tag.name for tag in tags))

    # Print unicode list of tags
    def __unicode__(self):
        return listed(self._items, quote="'")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Tags Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test case from the config """
            self.testcase = Nitrate()._config.testcase
            self.performance = Nitrate()._config.performance

        def testTagging1(self):
            """ Untagging a test case """
            # Remove tag and check
            testcase = TestCase(self.testcase.id)
            testcase.tags.remove(Tag("TestTag"))
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(Tag("TestTag") not in testcase.tags)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(Tag("TestTag") not in testcase.tags)

        def testTagging2(self):
            """ Tagging a test case """
            # Add tag and check
            testcase = TestCase(self.testcase.id)
            testcase.tags.add(Tag("TestTag"))
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(Tag("TestTag") in testcase.tags)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(Tag("TestTag") in testcase.tags)

        def testTagging3(self):
            """ Untagging a test case """
            # Remove tag and check
            testcase = TestCase(self.testcase.id)
            testcase.tags.remove(Tag("TestTag"))
            testcase.update()
            # Check cache content
            testcase = TestCase(self.testcase.id)
            self.assertTrue(Tag("TestTag") not in testcase.tags)
            # Check server content
            Cache.clear()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(Tag("TestTag") not in testcase.tags)

        def test_performance_testcase_tags(self):
            """ Checking tags of test cases

            Test checks tags from a test cases present in a test plan.
            The problem in this case is separate fetching of tag names
            for every test case (one query per case).
            """
            start_time = time.time()
            for case in TestPlan(self.performance.testplan):
                log.info("{0}: {1}".format(case, case.tags))
            _print_time(time.time() - start_time)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Test Plan Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestPlan(Mutable):
    """
    Test plan.

    Provides test plan attributes and 'testruns' and 'testcases'
    properties, the latter as the default iterator.
    """

    _cache = {}
    _identifier_width = 5

    # List of all object attributes (used for init & expiration)
    _attributes = ["author", "caseplans" "children", "components", "name",
            "owner", "parent", "product", "status", "tags", "testcases",
            "testruns", "type", "version"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Plan Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"),
            doc="Test plan id.")
    author = property(_getter("author"),
            doc="Test plan author.")
    children = property(_getter("children"),
            doc="Child test plans.")
    components = property(_getter("components"),
            doc="Relevant components.")
    tags = property(_getter("tags"),
            doc="Attached tags.")
    testcases = property(_getter("testcases"),
            doc="Test cases linked to this plan.")
    caseplans = property(_getter("caseplans"),
            doc="Test case plan objects related to this plan.")
    testruns = property(_getter("testruns"),
            doc="Test runs related to this plan.")

    # Read-write properties
    name = property(_getter("name"), _setter("name"),
            doc="Test plan name.")
    owner = property(_getter("owner"), _setter("owner"),
            doc="Test plan owner.")
    parent = property(_getter("parent"), _setter("parent"),
            doc="Parent test plan.")
    product = property(_getter("product"), _setter("product"),
            doc="Test plan product.")
    type = property(_getter("type"), _setter("type"),
            doc="Test plan type.")
    status = property(_getter("status"), _setter("status"),
            doc="Test plan status.")
    version = property(_getter("version"), _setter("version"),
            doc="Default product version.")

    @property
    def synopsis(self):
        """ One line test plan overview. """
        return "{0} - {1} ({2} cases, {3} runs)".format(self.identifier,
                self.name, len(self.testcases), len(self.testruns))

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # ID check
        if isinstance(id, int):
            return cls._cache[id], id

        # Check dictionary (only ID so far)
        if isinstance(id, dict):
            return cls._cache[id["plan_id"]], id["plan_id"]

        raise KeyError

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Plan Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None, product=None, version=None,
            type=None, **kwargs):
        """
        Initialize a test plan or create a new one.

        Provide id to initialize an existing test plan or name, product,
        version and type to create a new plan. Other parameters are optional.

            document .... Test plan document (default: '')
            parent ...... Parent test plan (object or id, default: None)

        Product, version and type can be provided as id, name or object.
        """

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id)
        if initialized: return
        Mutable.__init__(self, id, prefix="TP")

        # If inject given, fetch test case data from it
        if inject:
            self._fetch(inject)
        # Create a new test plan if name, type, product and version provided
        elif name and type and product and version:
            self._create(name=name, product=product, version=version,
                    type=type, **kwargs)
        # Otherwise just check that the test plan id was provided
        elif not id:
            raise NitrateError(
                    "Need either id or name, product, version "
                    "and type to initialize the test plan")

    def __iter__(self):
        """ Provide test cases as the default iterator. """
        for testcase in self.testcases:
            yield testcase

    def __unicode__(self):
        """ Test plan id & summary for printing. """
        return u"{0} - {1}".format(self.identifier, self.name)

    @staticmethod
    def search(**query):
        """ Search for test plans. """
        return [TestPlan(hash)
                for hash in Nitrate()._server.TestPlan.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Plan Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, name, product, version, type, **kwargs):
        """ Create a new test plan. """

        hash = {}

        # Name
        if name is None:
            raise NitrateError("Name required for creating new test plan")
        hash["name"] = name

        # Product
        if product is None:
            raise NitrateError("Product required for creating new test plan")
        elif isinstance(product, (int, basestring)):
            product = Product(product)
        hash["product"] = product.id

        # Version
        if version is None:
            raise NitrateError("Version required for creating new test plan")
        elif isinstance(version, int):
            version = Version(version)
        elif isinstance(version, basestring):
            version = Version(name=version, product=product)
        hash["default_product_version"] = version.id

        # Type
        if type is None:
            raise NitrateError("Type required for creating new test plan")
        elif isinstance(type, (int, basestring)):
            type = PlanType(type)
        hash["type"] = type.id

        # Parent
        parent = kwargs.get("parent")
        if parent is not None:
            if isinstance(parent, int):
                parent = TestPlan(parent)
            hash["parent"] = parent.id

        # Document - if not explicitly specified, put empty text
        hash["text"] = kwargs.get("document", " ")

        # Workaround for BZ#725995
        hash["is_active"] = "1"

        # Submit
        log.info("Creating a new test plan")
        log.xmlrpc(pretty(hash))
        inject = self._server.TestPlan.create(hash)
        log.xmlrpc(pretty(inject))
        try:
            self._id = inject["plan_id"]
        except TypeError:
            log.error("Failed to create a new test plan")
            log.error(pretty(hash))
            log.error(pretty(inject))
            raise NitrateError("Failed to create test plan")
        self._fetch(inject)
        log.info(u"Successfully created {0}".format(self))

    def _fetch(self, inject=None):
        """ Initialize / refresh test plan data.

        Either fetch them from the server or use provided hash.
        """
        Nitrate._fetch(self, inject)

        # Fetch the data hash from the server unless provided
        if inject is None:
            log.info("Fetching test plan " + self.identifier)
            inject = self._server.TestPlan.get(self.id)
            self._inject = inject
        # Otherwise just initialize the id from inject
        else:
            self._id = inject["plan_id"]
        log.debug("Initializing test plan " + self.identifier)
        log.xmlrpc(pretty(inject))
        if not "plan_id" in inject:
            log.error(pretty(inject))
            raise NitrateError("Failed to initialize " + self.identifier)

        # Set up attributes
        self._author = User(inject["author_id"])
        if inject["owner_id"] is not None:
            self._owner = User(inject["owner_id"])
        else:
            self._owner = None
        self._name = inject["name"]
        self._product = Product({
                "id": inject["product_id"],
                "name": inject["product"]})
        self._version = Version({
                "id": inject["product_version_id"],
                "value": inject["product_version"],
                "product_id": inject["product_id"]})
        self._type = PlanType(inject["type_id"])
        self._status = PlanStatus(inject["is_active"] in ["True", True])
        if inject["parent_id"] is not None:
            self._parent = TestPlan(inject["parent_id"])
        else:
            self._parent = None

        # Initialize containers
        self._testcases = PlanCases(self)
        self._caseplans = PlanCasePlans(self)
        self._testruns = PlanRuns(self)
        self._components = PlanComponents(self)
        self._children = ChildPlans(self)
        # If all tags are cached, initialize them directly from the inject
        if Tag._is_cached(inject["tag"]):
            self._tags = PlanTags(
                    self, inset=[Tag(tag) for tag in inject["tag"]])
        else:
            self._tags = PlanTags(self)

        # Index the fetched object into cache
        self._index()

    def _update(self):
        """ Save test plan data to the server. """

        # Prepare the update hash
        hash = {}
        hash["name"] = self.name
        hash["product"] = self.product.id
        hash["type"] = self.type.id
        hash["is_active"] = self.status.id == 1
        if self.parent is not None:
            hash["parent"] = self.parent.id
        hash["default_product_version"] = self.version.id
        if self.owner is not None:
            hash["owner"] = self.owner.id

        log.info("Updating test plan " + self.identifier)
        log.xmlrpc(pretty(hash))
        self._multicall.TestPlan.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._tags is not NitrateNone:
            self.tags.update()
        if self._testcases is not NitrateNone:
            self.testcases.update()
        if self._caseplans is not NitrateNone:
            self.caseplans.update()
        if self._testruns is not NitrateNone:
            self.testruns.update()
        if self._components is not NitrateNone:
            self.components.update()
        if self._children is not NitrateNone:
            self.children.update()

        # Update self (if modified)
        Mutable.update(self)

    def sortkey(self, testcase, sortkey=None):
        """ Get or set sortkey for given test case """
        # Make sure the test case we got belongs to the test plan
        if testcase not in self.testcases:
            raise NitrateError("Test case {0} not in test plan {1}".format(
                testcase.identifier, self.identifier))
        # Pick the correct CasePlan object
        try:
            caseplan = [caseplan for caseplan in self.caseplans
                    if caseplan.testcase == testcase][0]
        except KeyError:
            raise NitrateError("No CasePlan for {0} in {1} found".format(
                    testcase.identifier, self.identifier))
        # Modify the sortkey if requested
        if sortkey is not None:
            caseplan.sortkey = sortkey
        # And finally return the current value
        return caseplan.sortkey

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Plan Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan
            self.requests = Nitrate._requests
            self.cache_level = get_cache_level()
            Cache.clear()

        def tierDown(self):
            """ Restore cache level """
            set_cache_level(self.cache_level)

        def test_create_invalid(self):
            """ Create a new test plan (missing required parameters) """
            self.assertRaises(NitrateError, TestPlan, name="Test plan")

        def test_create_valid(self):
            """ Create a new test plan (valid) """
            testplan = TestPlan(
                    name="Test plan",
                    type=self.testplan.type,
                    product=self.testplan.product,
                    version=self.testplan.version)
            self.assertTrue(isinstance(testplan, TestPlan))
            self.assertEqual(testplan.name, "Test plan")

        def test_get_by_id(self):
            """ Fetch an existing test plan by id """
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(isinstance(testplan, TestPlan))
            self.assertEqual(testplan.name, self.testplan.name)
            self.assertEqual(testplan.type.name, self.testplan.type)
            self.assertEqual(testplan.product.name, self.testplan.product)
            self.assertEqual(testplan.version.name, self.testplan.version)
            self.assertEqual(testplan.owner.login, self.testplan.owner)

        def test_plan_status(self):
            """ Test read/write access to the test plan status """
            # Prepare original and negated status
            original = PlanStatus(self.testplan.status)
            negated = PlanStatus(not original.id)
            # Test original value
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.status, original)
            testplan.status = negated
            testplan.update()
            del testplan
            # Test negated value
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.status, negated)
            testplan.status = original
            testplan.update()
            del testplan
            # Back to the original value
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.status, original)

        def test_cache_none(self):
            """ Cache none """
            # Fetch test plan twice ---> two requests
            set_cache_level(CACHE_NONE)
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.name, self.testplan.name)
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.name, self.testplan.name)
            self.assertEqual(Nitrate._requests, self.requests + 2)

        def test_cache_objects(self):
            """ Cache objects """
            # Fetch test plan twice --->  just one request
            set_cache_level(CACHE_OBJECTS)
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.name, self.testplan.name)
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.name, self.testplan.name)
            self.assertEqual(Nitrate._requests, self.requests + 1)

        def test_cache_persistent(self):
            """ Cache persistent """
            set_cache_level(CACHE_PERSISTENT)
            # Fetch the test plan (populate the cache)
            testplan = TestPlan(self.testplan.id)
            log.debug(testplan.name)
            # Save, clear & load cache
            Cache.save()
            Cache.clear()
            Cache.load()
            requests = Nitrate._requests
            # Fetch once again ---> no additional request
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.name, self.testplan.name)
            self.assertEqual(Nitrate._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Plans Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CasePlans(Container):
    """ Test plans linked to a test case. """

    _cache = {}

    # Class of contained objects
    _class = TestPlan

    def _fetch(self, inset=None):
        """ Fetch currently attached tags from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s plans".format(self._identifier))
        self._current = set([TestPlan(hash)
                    for hash in self._server.TestCase.get_plans(self.id)])
        self._original = set(self._current)

    def _add(self, plans):
        """ Link provided plans to the test case. """
        log.info("Linking {1} to {0}".format(self._identifier,
                    listed([plan.identifier for plan in plans])))
        self._server.TestCase.link_plan(self.id, [plan.id for plan in plans])

    def _remove(self, plans):
        """ Unlink provided plans from the test case. """
        for plan in plans:
            log.info("Unlinking {0} from {1}".format(
                    plan.identifier, self._identifier))
            self._server.TestCase.unlink_plan(self.id, plan.id)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Test Run Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestRun(Mutable):
    """
    Test run.

    Provides test run attributes and 'caseruns' property containing all
    relevant case runs (which is also the default iterator).
    """

    _cache = {}
    _identifier_width = 6

    # List of all object attributes (used for init & expiration)
    _attributes = ["build", "caseruns", "errata", "finished", "manager",
            "notes", "product", "started", "status", "summary", "tags",
            "tester", "testcases", "testplan", "time"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Run Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"),
            doc="Test run id.")
    testplan = property(_getter("testplan"),
            doc="Test plan related to this test run.")
    tags = property(_getter("tags"),
            doc="Attached tags.")
    started = property(_getter("started"),
            doc="Timestamp when the test run was started (datetime).")
    finished = property(_getter("finished"),
            doc="Timestamp when the test run was finished (datetime).")
    caseruns = property(_getter("caseruns"),
            doc="CaseRun objects related to this test run.")
    testcases = property(_getter("testcases"),
            doc="""TestCase objects related to this test run\n
            Supports common container methods add(), remove() and clear()
            for adding and removing testcases to/from the test run.""")

    # Read-write properties
    build = property(_getter("build"), _setter("build"),
            doc="Build relevant for this test run.")
    manager = property(_getter("manager"), _setter("manager"),
            doc="Manager responsible for this test run.")
    notes = property(_getter("notes"), _setter("notes"),
            doc="Test run notes.")
    status = property(_getter("status"), _setter("status"),
            doc="Test run status")
    summary = property(_getter("summary"), _setter("summary"),
            doc="Test run summary.")
    tester = property(_getter("tester"), _setter("tester"),
            doc="Default tester.")
    time = property(_getter("time"), _setter("time"),
            doc="Estimated time.")
    errata = property(_getter("errata"), _setter("errata"),
            doc="Errata related to this test run.")

    @property
    def synopsis(self):
        """ One-line test run overview. """
        return "{0} - {1} ({2} cases)".format(
                self.identifier, self.summary, len(self.caseruns))

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # ID check
        if isinstance(id, int):
            return cls._cache[id], id

        # Check dictionary (only ID so far)
        if isinstance(id, dict):
            return cls._cache[id["run_id"]], id["run_id"]

        raise KeyError

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Run Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, testplan=None, **kwargs):
        """ Initialize a test run or create a new one.

        Initialize an existing test run if id provided, otherwise create
        a new test run based on specified test plan (required). Other
        parameters are optional and have the following defaults:

            build ....... "unspecified"
            errata....... related errata
            product ..... test run product
            version ..... test run product version
            summary ..... <test plan name> on <build>
            notes ....... ""
            manager ..... current user
            tester ...... current user
            tags ........ None
            testcases ... test cases to be included

        Tags should be provided as a list of tag names. Test cases can
        be provided as a list of test case objects or a list of ids. By
        default all CONFIRMED test cases are linked to the created run.
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id)
        if initialized: return
        Mutable.__init__(self, id, prefix="TR")

        # If inject given, fetch test case data from it
        if inject:
            self._fetch(inject)
        # Create a new test run based on provided plan
        elif testplan:
            self._create(testplan=testplan, **kwargs)
        # Otherwise just check that the test run id was provided
        elif not id:
            raise NitrateError(
                    "Need either id or test plan to initialize the test run")

    def __iter__(self):
        """ Provide test case runs as the default iterator. """
        for caserun in self.caseruns:
            yield caserun

    def __unicode__(self):
        """ Test run id & summary for printing. """
        return u"{0} - {1}".format(self.identifier, self.summary)

    @staticmethod
    def search(**query):
        """ Search for test runs. """
        return [TestRun(hash)
                for hash in Nitrate()._server.TestRun.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Run Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, testplan, product=None, version=None, build=None,
            summary=None, notes=None, manager=None, tester=None, tags=None,
            errata=None, testcases=None, **kwargs):
        """ Create a new test run. """

        hash = {}

        # Test plan
        if isinstance(testplan, int):
            testplan = TestPlan(testplan)
        hash["plan"] = testplan.id

        # Product & version
        if product is None:
            product = testplan.product
        elif not isinstance(product, Product):
            product = Product(product)
        hash["product"] = product.id
        if version is None:
            version = testplan.version
        elif isinstance(version, int):
            version = Version(version)
        else:
            version = Version(name=version, product=product)
        hash["product_version"] = version.id

        # Build & errata
        if build is None:
            build = "unspecified"
        if isinstance(build, basestring):
            build = Build(build=build, product=product)
        hash["build"] = build.id
        hash["errata_id"] = errata

        # Summary & notes
        if summary is None:
            summary = "{0} on {1}".format(testplan.name, build)
        if notes is None:
            notes = ""
        hash["summary"] = summary
        hash["notes"] = notes

        # Manager & tester (current user by default)
        if not isinstance(manager, User):
            manager = User(manager)
        if not isinstance(tester, User):
            tester = User(tester)
        hash["manager"] = manager.id
        hash["default_tester"] = tester.id

        # Prepare the list of test cases to be included in the test run
        # If testcases parameter is non-empty only selected cases will
        # be added, otherwise all CONFIRMED cases will be linked.
        if testcases is not None:
            hash["case"] = [case.id if isinstance(case, TestCase) else case
                    for case in testcases]
        else:
            hash["case"] = [case.id for case in testplan
                    if case.status == CaseStatus("CONFIRMED")]

        # Tag with supplied tags
        if tags: hash["tag"] = ",".join(tags)

        # Submit to the server and initialize
        log.info(u"Creating a new test run based on {0}".format(testplan))
        log.xmlrpc(pretty(hash))
        testrunhash = self._server.TestRun.create(hash)
        log.xmlrpc(pretty(testrunhash))
        try:
            self._id = testrunhash["run_id"]
        except TypeError:
            log.error(u"Failed to create a new test run based on {0}".format(
                    testplan))
            log.error(pretty(hash))
            log.error(pretty(testrunhash))
            raise NitrateError("Failed to create test run")
        self._fetch(testrunhash)
        # Add newly created test run to testplan.testruns container
        if PlanRuns._is_cached(testplan.testruns):
            testplan.testruns._fetch(list(testplan.testruns) + [self])
        log.info(u"Successfully created {0}".format(self))

    def _fetch(self, inject=None):
        """ Initialize / refresh test run data.

        Either fetch them from the server or use the provided hash.
        """
        Nitrate._fetch(self, inject)

        # Fetch the data hash from the server unless provided
        if inject is None:
            log.info("Fetching test run {0}".format(self.identifier))
            inject = self._server.TestRun.get(self.id)
            self._inject = inject
        else:
            self._id = inject["run_id"]
        log.debug("Initializing test run {0}".format(self.identifier))
        log.xmlrpc(pretty(inject))

        # Set up attributes
        self._build = Build(inject["build_id"])
        self._manager = User(inject["manager_id"])
        self._notes = inject["notes"]
        self._status = RunStatus(inject["stop_date"])
        self._summary = inject["summary"]
        self._tester = User(inject["default_tester_id"])
        self._testplan = TestPlan(inject["plan_id"])
        self._time = inject["estimated_time"]
        self._errata = inject["errata_id"]
        try:
            self._started = datetime.datetime.strptime(
                    inject["start_date"], "%Y-%m-%d %H:%M:%S")
        except TypeError:
            self._started = None
        try:
            self._finished = datetime.datetime.strptime(
                    inject["stop_date"], "%Y-%m-%d %H:%M:%S")
        except TypeError:
            self._finished = None

        # Initialize containers
        self._caseruns = RunCaseRuns(self)
        self._testcases = RunCases(self)
        # If all tags are cached, initialize them directly from the inject
        if Tag._is_cached(inject["tag"]):
            self._tags = RunTags(
                    self, inset=[Tag(tag) for tag in inject["tag"]])
        else:
            self._tags = RunTags(self)

        # Index the fetched object into cache
        self._index()

    def _update(self):
        """ Save test run data to the server. """

        # Prepare the update hash
        hash = {}
        hash["build"] = self.build.id
        hash["default_tester"] = self.tester.id
        hash["estimated_time"] = self.time
        hash["manager"] = self.manager.id
        hash["notes"] = self.notes
        hash["errata_id"] = self.errata
        # This is required until BZ#731982 is fixed
        hash["product"] = self.build.product.id
        hash["status"] = self.status.id
        hash["summary"] = self.summary

        log.info("Updating test run " + self.identifier)
        log.xmlrpc(pretty(hash))
        self._multicall.TestRun.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._tags is not NitrateNone:
            self.tags.update()
        if self._caseruns is not NitrateNone:
            self._caseruns.update()
        if self._testcases is not NitrateNone:
            self._testcases.update()

        # Update self (if modified)
        Mutable.update(self)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Run Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan
            self.testcase = Nitrate()._config.testcase
            self.testrun = Nitrate()._config.testrun

        def testCreateInvalid(self):
            """ Create a new test run (missing required parameters) """
            self.assertRaises(NitrateError, TestRun, summary="Test run")

        def testCreateValid(self):
            """ Create a new test run (valid) """
            testrun = TestRun(summary="Test run", testplan=self.testplan.id)
            self.assertTrue(isinstance(testrun, TestRun))
            self.assertEqual(testrun.summary, "Test run")

        def testCreateOptionalFields(self):
            """ Create a new test run, including optional fields """
            testrun = TestRun(
                    summary="Test run", testplan=self.testplan.id, errata=1234)
            self.assertTrue(isinstance(testrun, TestRun))
            self.assertEqual(testrun.summary, "Test run")
            self.assertEqual(testrun.errata, 1234)

        def testGetById(self):
            """ Fetch an existing test run by id """
            testrun = TestRun(self.testrun.id)
            self.assertTrue(isinstance(testrun, TestRun))
            self.assertEqual(testrun.summary, self.testrun.summary)
            self.assertEqual(str(testrun.started), self.testrun.started)
            self.assertEqual(str(testrun.finished), self.testrun.finished)

        def testErrata(self):
            """ Set, get and change errata """
            for errata in [111, 222, 333]:
                # Update the errata field, push to the server
                testrun = TestRun(self.testrun.id)
                testrun.errata = errata
                testrun.update()
                # Fetch the test run again, check for correct errata
                testrun = TestRun(self.testrun.id)
                self.assertEqual(testrun.errata, errata)

        def testDisabledCasesOmitted(self):
            """ Disabled test cases should be omitted """
            # Prepare disabled test case
            testcase = TestCase(self.testcase.id)
            original = testcase.status
            testcase.status = CaseStatus("DISABLED")
            testcase.update()
            # Create the test run, make sure the test case is not there
            testrun = TestRun(testplan=self.testplan.id)
            self.assertTrue(testcase.id not in
                    [caserun.testcase.id for caserun in testrun])
            # Restore the original status
            testcase.status = original
            testcase.update()

        def test_include_only_selected_cases(self):
            """ Include only selected test cases in the new run """
            testcase = TestCase(self.testcase.id)
            testplan = TestPlan(self.testplan.id)
            # No test case should be linked
            testrun = TestRun(testplan=testplan, testcases=[])
            self.assertTrue(testcase.id not in
                    [caserun.testcase.id for caserun in testrun])
            # Select test case by test case object
            testrun = TestRun(testplan=testplan, testcases=[testcase])
            self.assertTrue(testcase.id in
                    [caserun.testcase.id for caserun in testrun])
            # Select test case by id
            testrun = TestRun(testplan=testplan, testcases=[testcase.id])
            self.assertTrue(testcase.id in
                    [caserun.testcase.id for caserun in testrun])

        def testTestRunCaching(self):
            """ Test caching in TestRun class """
            TestRun._cache = {}
            requests = Nitrate._requests
            # Turn off caching
            set_cache_level(CACHE_NONE)
            testrun = TestRun(self.testrun.id)
            log.info(testrun.summary)
            testrun = TestRun(self.testrun.id)
            log.info(testrun.summary)
            self.assertEqual(Nitrate._requests, requests + 2)
            # Turn on caching
            TestRun._cache = {}
            set_cache_level(CACHE_OBJECTS)
            testrun = TestRun(self.testrun.id)
            log.info(testrun.summary)
            testrun = TestRun(self.testrun.id)
            log.info(testrun.summary)
            self.assertEqual(Nitrate._requests, requests + 3)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Runs Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanRuns(Container):
    """ Test runs related to a test plan """

    # Local cache of test runs for a test plan
    _cache = {}

    # Class of contained objects
    _class = TestRun

    def _fetch(self, inset=None):
        """ Fetch test runs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching testruns for {0}".format(self._identifier))
        injects = self._server.TestPlan.get_test_runs(self.id)
        log.xmlrpc(pretty(injects))
        self._current = set([TestRun(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, testruns):
        """ New test runs are created using TestRun() constructor """
        raise NitrateError(
                "Use TestRun(testplan=X) for creating a new test run")

    def _remove(self, testruns):
        """ Currently no support for removing test runs from test plans """
        raise NitrateError("Sorry, no support for removing test runs yet")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Run Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan
            self.testrun = Nitrate()._config.testrun

        def test_inclusion(self):
            """ Test run included in the container"""
            testplan = TestPlan(self.testplan.id)
            testrun = TestRun(self.testrun.id)
            self.assertTrue(testrun in testplan.testruns)
            # Everything should be kept in the persistent cache
            if _cache_level >= CACHE_PERSISTENT:
                Cache.save()
                Cache.clear()
                Cache.load()
                requests = Nitrate._requests
                testplan = TestPlan(self.testplan.id)
                testrun = TestRun(self.testrun.id)
                self.assertTrue(testrun in testplan.testruns)
                self.assertEqual(requests, Nitrate._requests)

        def test_new_test_run(self):
            """ New test runs should be linked """
            testplan = TestPlan(self.testplan.id)
            testrun = TestRun(testplan=testplan)
            self.assertTrue(testrun in testplan.testruns)
            # Everything should be kept in the persistent cache
            if _cache_level >= CACHE_PERSISTENT:
                Cache.save()
                Cache.clear()
                Cache.load()
                requests = Nitrate._requests
                testplan = TestPlan(self.testplan.id)
                testrun = TestRun(self.testrun.id)
                self.assertTrue(testrun in testplan.testruns)
                self.assertEqual(requests, Nitrate._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Test Case Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestCase(Mutable):
    """
    Test case.

    Provides test case attributes and 'testplans' property as the
    default iterator. Furthermore contains bugs, components and tags
    properties.
    """

    _cache = {}
    _identifier_width = 7

    # List of all object attributes (used for init & expiration)
    _attributes = ["arguments", "author", "automated", "autoproposed", "bugs",
            "category", "components", "created", "link", "manual", "notes",
            "plans", "priority", "script", "sortkey", "status", "summary",
            "tags", "tester", "testplans", "time"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"),
            doc="Test case id (read-only).")
    author = property(_getter("author"),
            doc="Test case author.")
    created = property(_getter("created"),
            doc="Test case creation date (datetime).")
    tags = property(_getter("tags"),
            doc="Attached tags.")
    bugs = property(_getter("bugs"),
            doc="Attached bugs.")
    testplans = property(_getter("testplans"),
            doc="Test plans linked to this test case.")
    components = property(_getter("components"),
            doc="Components related to this test case.")

    @property
    def synopsis(self):
        """ Short summary about the test case. """
        plans = len(self.testplans)
        return "{0} ({1}, {2}, {3}, {4} {5})".format(
                self, self.category, self.priority, self.status,
                plans, "test plan" if plans == 1 else "test plans")

    # Read-write properties
    automated = property(_getter("automated"), _setter("automated"),
            doc="Automation flag. True if the test case is automated.")
    autoproposed = property(_getter("autoproposed"), _setter("autoproposed"),
            doc="True if the test case is proposed for automation.")
    arguments = property(_getter("arguments"), _setter("arguments"),
            doc="Test script arguments (used for automation).")
    category = property(_getter("category"), _setter("category"),
            doc="Test case category.")
    link = property(_getter("link"), _setter("link"),
            doc="Test case reference link.")
    manual = property(_getter("manual"), _setter("manual"),
            doc="Manual flag. True if the test case is manual.")
    notes = property(_getter("notes"), _setter("notes"),
            doc="Test case notes.")
    priority = property(_getter("priority"), _setter("priority"),
            doc="Test case priority.")
    requirement = property(_getter("requirement"), _setter("requirement"),
            doc="Test case requirements.")
    script = property(_getter("script"), _setter("script"),
            doc="Test script (used for automation).")
    # XXX sortkey = property(_getter("sortkey"), _setter("sortkey"),
    #        doc="Sort key.")
    status = property(_getter("status"), _setter("status"),
            doc="Current test case status.")
    summary = property(_getter("summary"), _setter("summary"),
            doc="Summary describing the test case.")
    tester = property(_getter("tester"), _setter("tester"),
            doc="Default tester.")
    time = property(_getter("time"), _setter("time"),
            doc="Estimated time.")

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # ID check
        if isinstance(id, int):
            return cls._cache[id], id

        # Check dictionary (only ID so far)
        if isinstance(id, dict):
            return cls._cache[id["case_id"]], id["case_id"]

        raise KeyError

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, summary=None, category=None, **kwargs):
        """ Initialize a test case or create a new one.

        Initialize an existing test case (if id provided) or create a
        new one (based on provided summary and category. Other optional
        parameters supported are:

            product ........ product (default: category.product)
            status ......... test case status (default: PROPOSED)
            automated ...... automation flag (default: True)
            autoproposed ... proposed for automation (default: False)
            manual ......... manual flag (default: False)
            priority ....... priority object, id or name (default: P3)
            script ......... test path (default: None)
            arguments ...... script arguments (default: None)
            requirement .... requirement (default: None)
            tester ......... user object or login (default: None)
            link ........... reference link (default: None)

        Examples:

            existing = TestCase(1234)
            sanity = Category(name="Sanity", product="Fedora")
            new = TestCase(summary="Test", category=sanity)
            new = TestCase(summary="Test", category="Sanity", product="Fedora")

        Note: When providing category by name specify product as well.
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id)
        if initialized: return
        Mutable.__init__(self, id, prefix="TC")

        # If inject given, fetch test case data from it
        if inject:
            self._fetch(inject)
        # Create a new test case based on summary and category
        elif summary and category:
            self._create(summary=summary, category=category, **kwargs)
        # Otherwise just check that the test case id was provided
        elif not id:
            raise NitrateError("Need either id or both summary and category "
                    "to initialize the test case")

    def __unicode__(self):
        """ Test case id & summary for printing. """
        return u"{0} - {1}".format(self.identifier, self.summary)

    @staticmethod
    def search(**query):
        """ Search for test cases. """
        return [TestCase(hash)
                for hash in Nitrate()._server.TestCase.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, summary, category, **kwargs):
        """ Create a new test case. """

        hash = {}

        # Summary
        hash["summary"] = summary

        # If category provided as text, we need product as well
        product = kwargs.get("product")
        if isinstance(category, basestring) and not kwargs.get("product"):
            raise NitrateError(
                    "Need product when category specified by name")
        # Category & Product
        if isinstance(category, basestring):
            category = Category(category=category, product=product)
        elif not isinstance(category, Category):
            raise NitrateError("Invalid category '{0}'".format(category))
        hash["category"] = category.id
        hash["product"] = category.product.id

        # Priority
        priority = kwargs.get("priority")
        if priority is None:
            priority = Priority("P3")
        elif not isinstance(priority, Priority):
            priority = Priority(priority)
        hash["priority"] = priority.id

        # User
        tester = kwargs.get("tester")
        if tester:
            if isinstance(tester, basestring):
                tester = User(login=tester)
            hash["default_tester"] = tester.login

        # Script, arguments, requirement & reference link
        hash["script"] = kwargs.get("script")
        hash["arguments"] = kwargs.get("arguments")
        hash["requirement"] = kwargs.get("requirement")
        hash["extra_link"] = kwargs.get("link")

        # Case Status
        status = kwargs.get("status")
        if status:
            if isinstance(status, basestring):
                status = CaseStatus(status)
            hash["case_status"] = status.id

        # Manual, automated and autoproposed
        automated = kwargs.get("automated", True)
        autoproposed = kwargs.get("autoproposed", False)
        manual = kwargs.get("manual", False)
        if automated and manual:
            hash["is_automated"] = 2
        elif automated:
            hash["is_automated"] = 1
        else:
            hash["is_automated"] = 0
        hash["is_automated_proposed"] = autoproposed

        # Estimated time
        time = kwargs.get("time")
        if time is not None:
            hash["estimated_time"] = time

        # Notes
        notes = kwargs.get("notes")
        if notes:
            hash["notes"] = notes

        # Submit
        log.info("Creating a new test case")
        log.xmlrpc(pretty(hash))
        testcasehash = self._server.TestCase.create(hash)
        log.xmlrpc(pretty(testcasehash))
        try:
            self._id = testcasehash["case_id"]
        except TypeError:
            log.error("Failed to create a new test case")
            log.error(pretty(hash))
            log.error(pretty(testcasehash))
            raise NitrateError("Failed to create test case")
        self._fetch(testcasehash)
        log.info(u"Successfully created {0}".format(self))


    def _fetch(self, inject=None):
        """ Initialize / refresh test case data.

        Either fetch them from the server or use provided hash.
        """
        Nitrate._fetch(self, inject)

        # Fetch the data hash from the server unless provided
        if inject is None:
            log.info("Fetching test case " + self.identifier)
            inject = self._server.TestCase.get(self.id)
            self._inject = inject
        else:
            self._id = inject["case_id"]
        log.debug("Initializing test case " + self.identifier)
        log.xmlrpc(pretty(inject))

        # Set up attributes
        self._arguments = inject["arguments"]
        self._author = User(inject["author_id"])
        self._category = Category(inject["category_id"])
        self._created = datetime.datetime.strptime(
                inject["create_date"], "%Y-%m-%d %H:%M:%S")
        self._link = inject["extra_link"]
        self._notes = inject["notes"]
        self._priority = Priority(inject["priority_id"])
        self._requirement = inject["requirement"]
        self._script = inject["script"]
        # XXX self._sortkey = inject["sortkey"]
        self._status = CaseStatus(inject["case_status_id"])
        self._summary = inject["summary"]
        self._time = inject["estimated_time"]
        if inject["default_tester_id"] is not None:
            self._tester = User(inject["default_tester_id"])
        else:
            self._tester = None

        # Handle manual, automated and autoproposed
        self._automated = inject["is_automated"] in [1, 2]
        self._manual = inject["is_automated"] in [0, 2]
        self._autoproposed = inject["is_automated_proposed"]

        # Empty script or arguments to be handled same as None
        if self._script == "":
            self._script = None
        if self._arguments == "":
            self._arguments = None

        # Initialize containers
        self._bugs = CaseBugs(self)
        self._testplans = CasePlans(self)
        self._components = CaseComponents(self)
        # If all tags are cached, initialize them directly from the inject
        if Tag._is_cached(inject["tag"]):
            self._tags = CaseTags(
                    self, inset=[Tag(tag) for tag in inject["tag"]])
        else:
            self._tags = CaseTags(self)

        # Index the fetched object into cache
        self._index()

    def _update(self):
        """ Save test case data to server """
        hash = {}

        hash["arguments"] = self.arguments
        hash["case_status"] = self.status.id
        hash["category"] = self.category.id
        hash["estimated_time"] = self.time
        if self.automated and self.manual:
            hash["is_automated"] = 2
        elif self.automated:
            hash["is_automated"] = 1
        else:
            hash["is_automated"] = 0
        hash["is_automated_proposed"] = self.autoproposed
        hash["extra_link"] = self.link
        hash["notes"] = self.notes
        hash["priority"] = self.priority.id
        hash["product"] = self.category.product.id
        hash["requirement"] = self.requirement
        hash["script"] = self.script
        # XXX hash["sortkey"] = self.sortkey
        hash["summary"] = self.summary
        if self.tester:
            hash["default_tester"] = self.tester.login

        log.info("Updating test case " + self.identifier)
        log.xmlrpc(pretty(hash))
        self._multicall.TestCase.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._bugs is not NitrateNone:
            self.bugs.update()
        if self._tags is not NitrateNone:
            self.tags.update()
        if self._testplans is not NitrateNone:
            self.testplans.update()
        if self._components is not NitrateNone:
            self._components.update()

        # Update self (if modified)
        Mutable.update(self)


    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test case from the config """
            self.testcase = Nitrate()._config.testcase
            self.performance = Nitrate()._config.performance

        def testCreateInvalid(self):
            """ Create a new test case (missing required parameters) """
            self.assertRaises(
                    NitrateError, TestCase, summary="Test case summary")

        def testCreateValid(self):
            """ Create a new test case (valid) """
            case = TestCase(summary="Test case summary",
                    product="Red Hat Enterprise Linux 6", category="Sanity")
            self.assertTrue(
                    isinstance(case, TestCase), "Check created instance")
            self.assertEqual(case.summary, "Test case summary")
            self.assertEqual(case.priority, Priority("P3"))
            self.assertEqual(str(case.category), "Sanity")

        def testCreateValidWithOptionalFields(self):
            """ Create a new test case, include optional fields """
            # High-priority automated security-related test case
            case = TestCase(
                    summary="High-priority automated test case",
                    product=self.testcase.product,
                    category="Security",
                    automated=True,
                    manual=False,
                    autoproposed=False,
                    priority=Priority("P1"),
                    script="/path/to/test/script",
                    arguments="SOME_ARGUMENT=42",
                    requirement="dependency",
                    link="http://example.com/test-case-link")
            self.assertTrue(
                    isinstance(case, TestCase), "Check created instance")
            self.assertEqual(case.summary, "High-priority automated test case")
            self.assertEqual(case.script, "/path/to/test/script")
            self.assertEqual(case.arguments, "SOME_ARGUMENT=42")
            self.assertEqual(case.requirement, "dependency")
            self.assertEqual(case.link, "http://example.com/test-case-link")
            self.assertEqual(case.priority, Priority("P1"))
            self.assertTrue(case.automated)
            self.assertFalse(case.autoproposed)
            self.assertFalse(case.manual)
            # Low-priority manual sanity test case
            case = TestCase(
                    summary="Low-priority manual test case",
                    product=self.testcase.product,
                    category="Sanity",
                    manual=True,
                    autoproposed=True,
                    automated=False,
                    priority=Priority("P5"),
                    link="http://example.com/another-case-link")
            self.assertTrue(
                    isinstance(case, TestCase), "Check created instance")
            self.assertEqual(case.summary, "Low-priority manual test case")
            self.assertEqual(case.script, None)
            self.assertEqual(case.link, "http://example.com/another-case-link")
            self.assertEqual(case.priority, Priority("P5"))
            self.assertTrue(case.manual)
            self.assertTrue(case.autoproposed)
            self.assertFalse(case.automated)

        def testGetById(self):
            """ Fetch an existing test case by id """
            testcase = TestCase(self.testcase.id)
            self.assertTrue(isinstance(testcase, TestCase))
            self.assertEqual(testcase.summary, self.testcase.summary)
            self.assertEqual(testcase.category.name, self.testcase.category)
            created = datetime.datetime.strptime(
                    self.testcase.created, "%Y-%m-%d %H:%M:%S")
            self.assertEqual(testcase.created, created)

        def testGetByInvalidId(self):
            """ Fetch an existing test case by id (invalid id) """
            self.assertRaises(NitrateError, TestCase, 'invalid-id')

        def testReferenceLink(self):
            """ Fetch and update test case reference link """
            for url in ["http://first.host.com/", "http://second.host.com/"]:
                testcase = TestCase(self.testcase.id)
                testcase.link = url
                testcase.update()
                testcase = TestCase(self.testcase.id)
                self.assertEqual(testcase.link, url)

        def testAutomationFlags(self):
            """ Check automated, autoproposed and manual flags """
            # Both automated and manual
            for automated in [False, True]:
                for manual in [False, True]:
                    # Unsupported combination
                    if not automated and not manual:
                        continue
                    for autoproposed in [False, True]:
                        # Fetch and update
                        testcase = TestCase(self.testcase.id)
                        testcase.automated = automated
                        testcase.manual = manual
                        testcase.autoproposed = autoproposed
                        testcase.update()
                        # Reload and check
                        testcase = TestCase(self.testcase.id)
                        self.assertEqual(testcase.automated, automated)
                        self.assertEqual(testcase.autoproposed, autoproposed)
                        self.assertEqual(testcase.manual, manual)

        def testTestCaseCaching(self):
            """ Test caching in TestCase class """
            requests = Nitrate._requests
            # Turn off caching
            set_cache_level(CACHE_NONE)
            testcase = TestCase(self.testcase.id)
            log.info(testcase.summary)
            testcase = TestCase(self.testcase.id)
            log.info(testcase.summary)
            self.assertEqual(Nitrate._requests, requests + 2)
            # Turn on caching
            TestCase._cache = {}
            set_cache_level(CACHE_OBJECTS)
            testcase = TestCase(self.testcase.id)
            log.info(testcase.summary)
            testcase = TestCase(self.testcase.id)
            log.info(testcase.summary)
            self.assertEqual(Nitrate._requests, requests + 3)

        def test_performance_testcases_and_testers(self):
            """ Checking test cases and their default testers

            Test checks all test cases linked to specified test plan and
            displays the result with their testers. The slowdown here is
            fetching users from the database (one by one).
            """
            start_time = time.time()
            for testcase in TestPlan(self.performance.testplan):
                log.info("{0}: {1}".format(testcase.tester, testcase))
            _print_time(time.time() - start_time)

        def test_performance_testcases_and_testplans(self):
            """ Checking test plans linked to test cases

            Test checks test cases and plans which contain these test
            cases.  The main problem is fetching the same test plans
            multiple times if they contain more than one test case in
            the set.
            """
            start_time = time.time()
            for testcase in TestPlan(self.performance.testplan):
                log.info("{0} is in test plans:".format(testcase))
                for testplan in testcase.testplans:
                    log.info("  {0}".format(testplan.name))
            _print_time(time.time() - start_time)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Test Cases Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanCases(Container):
    """ Test cases linked to a test plan. """

    _cache = {}

    # Class of contained objects
    _class = TestCase

    def _fetch(self, inset=None):
        """ Fetch currently linked test cases from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s cases".format(self._identifier))
        # Fetch test cases from the server
        injects = self._server.TestPlan.get_test_cases(self.id)
        log.xmlrpc("Fetched {0}".format(listed(injects, "inject")))
        self._current = set([TestCase(inject) for inject in injects])
        self._original = set(self._current)
        # Initialize case plans if not already cached
        if not PlanCasePlans._is_cached(self._object.caseplans):
            inset = [CasePlan({
                    # Fake our own internal id from testplan & testcase
                    "id": _idify([self._object.id, inject["case_id"]]),
                    "case_id": inject["case_id"],
                    "plan_id": self._object.id,
                    "sortkey": inject["sortkey"]
                    }) for inject in injects]
            self._object.caseplans._fetch(inset)

    def _add(self, cases):
        """ Link provided cases to the test plan. """
        # Link provided cases on the server
        log.info("Linking {1} to {0}".format(self._identifier,
                    listed([case.identifier for case in cases])))
        self._server.TestCase.link_plan([case.id for case in cases], self.id)
        # Add corresponding CasePlan objects to the PlanCasePlans container
        if PlanCasePlans._is_cached(self._object.caseplans):
            self._object.caseplans.add([
                    CasePlan(testcase=case, testplan=self._object)
                    for case in cases])

    def _remove(self, cases):
        """ Unlink provided cases from the test plan. """
        # Unlink provided cases on the server
        for case in cases:
            log.info("Unlinking {0} from {1}".format(
                    case.identifier, self._identifier))
            self._server.TestCase.unlink_plan(case.id, self.id)
        # Add corresponding CasePlan objects from the PlanCasePlans container
        if PlanCasePlans._is_cached(self._object.caseplans):
            self._object.caseplans.remove([
                    CasePlan(testcase=case, testplan=self._object)
                    for case in cases])

    def __iter__(self):
        """ Iterate over all included test cases ordered by sortkey """
        for testcase in sorted(
                self._items, key=lambda x: self._object.sortkey(x)):
            yield testcase

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Child Plans
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ChildPlans(Container):
    """ Child test plans of a parent plan """

    _cache = {}

    # Class of contained objects
    _class = TestPlan

    def _fetch(self, inset=None):
        """ Find all child test plans """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset):
            return
        log.info("Fetching {0}'s child plans".format(self._identifier))
        self._current = set(TestPlan.search(parent=self.id))
        self._original = set(self._current)

    def _add(self, plans):
        """ Set self as parent of given test plans """
        log.info("Setting {1} as parent of {0}".format(self._identifier,
                listed([plan.identifier for plan in plans])))
        for plan in plans:
            plan.parent = TestPlan(self.id)
            plan.update()

    def _remove(self, plans):
        """ Remove self as parent of given test plans """
        log.info("Removing {1} as parent of {0}".format(self._identifier,
                listed([plan.identifier for plan in plans])))
        for plan in plans:
            plan.parent = None
            plan.update()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Child Plans Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan

        def test_add_and_remove_child_plan(self):
            """ Add and remove child test plan """
            parent = TestPlan(self.testplan.id)
            # Create a new separate plan, make sure it's not child
            child = TestPlan(name="Child test plan", type=parent.type,
                    product=parent.product, version=parent.version)
            self.assertTrue(child not in parent.children)
            # Add the new test plan to the children, reload, check
            parent.children.add(child)
            parent.update()
            parent = TestPlan(parent.id)
            self.assertTrue(child in parent.children)
            # Remove the child again, update, reload, check
            # FIXME Currently disabled because if BZ#885232
            #parent.children.remove(child)
            #parent.update()
            #parent = TestPlan(parent.id)
            #self.assertTrue(child not in parent.children)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Run Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseRun(Mutable):
    """
    Test case run.

    Provides case run attributes such as status and assignee, including
    the relevant 'testcase' object.
    """

    _identifier_width = 8

    # By default we do not cache CaseRun objects at all
    _expiration = NEVER_CACHE
    _cache = {}

    # List of all object attributes (used for init & expiration)
    _attributes = ["assignee", "bugs", "build", "notes", "sortkey", "status",
            "testcase", "testrun"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Run Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"),
            doc="Test case run id.")
    testcase = property(_getter("testcase"),
            doc = "Test case object.")
    testrun = property(_getter("testrun"),
            doc = "Test run object.")
    bugs = property(_getter("bugs"),
            doc = "Attached bugs.")

    # Read-write properties
    assignee = property(_getter("assignee"), _setter("assignee"),
            doc = "Test case run assignee object.")
    build = property(_getter("build"), _setter("build"),
            doc = "Test case run build object.")
    notes = property(_getter("notes"), _setter("notes"),
            doc = "Test case run notes (string).")
    sortkey = property(_getter("sortkey"), _setter("sortkey"),
            doc = "Test case sort key (int).")
    status = property(_getter("status"), _setter("status"),
            doc = "Test case run status object.")

    @classmethod
    def _cache_lookup(cls, id, **kwargs):
        """ Look up cached objects, return found instance and search key """
        # ID check
        if isinstance(id, int):
            return cls._cache[id], id

        # Check dictionary (only ID so far)
        if isinstance(id, dict):
            return cls._cache[id["case_run_id"]], id["case_run_id"]

        raise KeyError

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Run Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, testcase=None, testrun=None, **kwargs):
        """ Initialize a test case run or create a new one.

        Initialize an existing test case run (if id provided) or create
        a new test case run (based on provided test case and test run).
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id, **kwargs)
        if initialized: return
        Mutable.__init__(self, id, prefix="CR")

        # If inject given, fetch test case run data from it
        if inject:
            self._fetch(inject, **kwargs)
        # Create a new test case run based on case and run
        elif testcase and testrun:
            self._create(testcase=testcase, testrun=testrun, **kwargs)
        # Otherwise just check that the test case run id was provided
        elif not id:
            raise NitrateError("Need either id or testcase and testrun "
                    "to initialize the case run")

    def __unicode__(self):
        """ Case run id, status & summary for printing. """
        return u"{0} - {1} - {2}".format(
                self.status.shortname, self.identifier, self.testcase.summary)

    @staticmethod
    def search(**query):
        """ Search for case runs. """
        return [CaseRun(inject) for inject in
                Nitrate()._server.TestCaseRun.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Run Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, testcase, testrun, **kwargs):
        """ Create a new case run. """

        hash = {}

        # TestCase
        if testcase is None:
            raise NitrateError("Case ID required for new case run")
        elif isinstance(testcase, basestring):
            testcase = TestCase(testcase)
        hash["case"] = testcase.id

        # TestRun
        if testrun is None:
            raise NitrateError("Run ID required for new case run")
        elif isinstance(testrun, basestring):
            testrun = TestRun(testrun)
        hash["run"] = testrun.id

        # Build is required by XMLRPC
        build = testrun.build
        hash["build"] = build.id

        # Submit
        log.info("Creating new case run")
        log.xmlrpc(pretty(hash))
        inject = self._server.TestCaseRun.create(hash)
        log.xmlrpc(pretty(inject))
        try:
            self._id = inject["case_run_id"]
        except TypeError:
            log.error("Failed to create new case run")
            log.error(pretty(hash))
            log.error(pretty(inject))
            raise NitrateError("Failed to create case run")
        self._fetch(inject)
        log.info(u"Successfully created {0}".format(self))

        # And finally add to testcases and caseruns containers
        self.testrun.testcases._fetch(
                [self.testcase] + list(self.testrun.testcases))
        self.testrun.caseruns._fetch(
                [self] + list(self.testrun.caseruns))

    def _fetch(self, inject=None, **kwargs):
        """ Initialize / refresh test case run data.

        Either fetch them from the server or use the supplied hashes.
        """
        Nitrate._fetch(self, inject)

        # Fetch the data from the server unless inject provided
        if inject is None:
            log.info("Fetching case run {0}".format(self.identifier))
            inject = self._server.TestCaseRun.get(self.id)
            self._inject = inject
        else:
            self._id = inject["case_run_id"]
        log.debug("Initializing case run {0}".format(self.identifier))
        log.xmlrpc(pretty(inject))

        # Set up attributes
        self._assignee = User(inject["assignee_id"])
        self._build = Build(inject["build_id"])
        self._notes = inject["notes"]
        if inject["sortkey"] is not None:
            self._sortkey = int(inject["sortkey"])
        else:
            self._sortkey = None
        self._status = Status(inject["case_run_status_id"])
        self._testrun = TestRun(inject["run_id"])
        # Initialize attached test case (from dict, object or id)
        testcaseinject = kwargs.get("testcaseinject", None)
        if testcaseinject and isinstance(testcaseinject, dict):
            self._testcase = TestCase(testcaseinject)
        elif testcaseinject and isinstance(testcaseinject, TestCase):
            self._testcase = testcaseinject
        else:
            self._testcase = TestCase(inject["case_id"])

        # Initialize containers
        self._bugs = CaseRunBugs(self)

        # Index the fetched object into cache
        self._index()

    def _update(self):
        """ Save test case run data to the server. """

        # Prepare the update hash
        hash = {}
        hash["build"] = self.build.id
        hash["assignee"] = self.assignee.id
        hash["case_run_status"] = self.status.id
        hash["notes"] = self.notes
        hash["sortkey"] = self.sortkey

        # Work around BZ#715596
        if self.notes is None: hash["notes"] = ""

        log.info("Updating case run " + self.identifier)
        log.xmlrpc(pretty(hash))
        self._multicall.TestCaseRun.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._bugs is not NitrateNone:
            self.bugs.update()

        # Update self (if modified)
        Mutable.update(self)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Runs Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up performance test configuration from the config """
            self.performance = Nitrate()._config.performance

        def test_performance_update_caseruns(self):
            """ Updating multiple CaseRun statuses (MultiCall off)

            Test for fetching caserun states and updating them focusing
            on the updating part. The performance issue is isolated
            CaseRun state update.
            """
            start_time = time.time()
            for caserun in TestRun(self.performance.testrun):
                log.info("{0} {1}".format(caserun.id, caserun.status))
                caserun.status = Status(random.randint(1,8))
                caserun.update()
            _print_time(time.time() - start_time)

        def test_performance_update_caseruns_multicall(self):
            """ Updating multiple CaseRun statuses (MultiCall on)

            Test for fetching caserun states and updating them focusing
            on the updating part with MultiCall.
            """
            multicall_start()
            start_time = time.time()
            for caserun in TestRun(self.performance.testrun):
                log.debug("{0} {1}".format(caserun.id, caserun.status))
                caserun.status = Status(random.randint(1,8))
                caserun.update()
            multicall_end()
            _print_time(time.time() - start_time)

        def test_performance_testcases_in_caseruns(self):
            """ Checking CaseRuns in TestRuns in TestPlans

            Test for checking test cases that test run contains in
            specified test plan(s) that are children of a master
            test plan. The delay is caused by repeatedly fetched testcases
            connected to case runs (although some of them may have already
            been fetched).
            """
            start_time = time.time()
            for testplan in TestPlan(self.performance.testplan).children:
                log.info("{0}".format(testplan.name))
                for testrun in testplan.testruns:
                    log.info("  {0} {1} {2}".format(
                            testrun, testrun.manager, testrun.status))
                    for caserun in testrun.caseruns:
                        log.info("    {0} {1} {2}".format(
                                caserun, caserun.testcase, caserun.status))
            _print_time(time.time() - start_time)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCases Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunCases(Container):
    """ Test case objects related to a test run """

    # Local cache of test cases for a test run
    _cache = {}

    # Class of contained objects
    _class = TestCase

    def _fetch(self, inset=None):
        """ Fetch test run cases from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset): return
        # Fetch attached test cases from the server
        log.info("Fetching {0}'s test cases".format(self._identifier))
        injects = self._server.TestRun.get_test_cases(self.id)
        self._current = set([TestCase(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, testcases):
        """ Add given test cases to the test run """
        # Short info about the action
        identifiers = [testcase.identifier for testcase in testcases]
        log.info("Adding {0} to {1}".format(
                listed(identifiers, "testcase", max=3),
                self._object.identifier))
        # Prepare data and push
        data = [testcase.id for testcase in testcases]
        log.xmlrpc(pretty(data))
        self._server.TestRun.add_cases(self.id, data)
        # RunCaseRuns will need update ---> erase current data
        self._object.caseruns._init()

    def _remove(self, testcases):
        """ Remove given test cases from the test run """
        # Short info about the action
        identifiers = [testcase.identifier for testcase in testcases]
        log.info("Removing {0} from {1}".format(
                listed(identifiers, "testcase", max=3),
                self._object.identifier))
        data = [testcase.id for testcase in testcases]
        log.xmlrpc(pretty(data))
        self._server.TestRun.remove_cases(self.id, data)
        # RunCaseRuns will need update ---> erase current data
        self._object.caseruns._init()

    def __iter__(self):
        """ Iterate over all included test cases ordered by sortkey """
        for caserun in sorted(self._object.caseruns, key=lambda x: x.sortkey):
            yield caserun.testcase

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  RunCases Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan
            self.testrun = Nitrate()._config.testrun
            self.testcase = Nitrate()._config.testcase

        def test_present(self):
            """ Check test case presence """
            testcase = TestCase(self.testcase.id)
            testrun = TestRun(self.testrun.id)
            self.assertTrue(testcase in testrun.testcases)
            self.assertTrue(testcase in
                    [caserun.testcase for caserun in testrun.caseruns])

        def test_add_remove(self):
            """ Add and remove test case """
            # Create a new test run, make sure our test case is there
            testcase = TestCase(self.testcase.id)
            testrun = TestRun(testplan=self.testplan.id)
            self.assertTrue(testcase in testrun.testcases)
            # Remove and check it's not either in testcases or caseruns
            testrun.testcases.remove(testcase)
            testrun.update()
            self.assertTrue(testcase not in testrun.testcases)
            self.assertTrue(testcase not in
                    [caserun.testcase for caserun in testrun.caseruns])
            # Now make sure the same data reached the server as well
            if _cache_level >= CACHE_OBJECTS:
                Cache.clear([RunCases, RunCaseRuns])
            testrun = TestRun(testrun.id)
            self.assertTrue(testcase not in testrun.testcases)
            self.assertTrue(testcase not in
                    [caserun.testcase for caserun in testrun.caseruns])
            # Add back and check it's in both testcases or caseruns
            testrun.testcases.add(testcase)
            testrun.update()
            self.assertTrue(testcase in testrun.testcases)
            self.assertTrue(testcase in
                    [caserun.testcase for caserun in testrun.caseruns])
            # Again make sure the same data reached the server as well
            if _cache_level >= CACHE_OBJECTS:
                Cache.clear([RunCases, RunCaseRuns])
            testrun = TestRun(testrun.id)
            self.assertTrue(testcase in testrun.testcases)
            self.assertTrue(testcase in
                    [caserun.testcase for caserun in testrun.caseruns])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCaseRuns Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunCaseRuns(Container):
    """ Test case run objects related to a test run """

    # Local cache of test case runs for a test run
    _cache = {}

    # Class of contained objects
    _class = CaseRun

    def _fetch(self, inset=None):
        """ Fetch case runs from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset): return
        # Fetch test case runs from the server
        log.info("Fetching {0}'s case runs".format(self._identifier))
        injects = self._server.TestRun.get_test_case_runs(self.id)
        # Feed the TestRun.testcases container with the initial object
        # set if all cases are already cached (saving unnecesary fetch)
        testcaseids = [inject["case_id"] for inject in injects]
        if (not RunCases._is_cached(self._object.testcases) and
                TestCase._is_cached(testcaseids)):
            self._object.testcases._fetch([TestCase(id) for id in testcaseids])
        # And finally create the initial object set
        self._current = set([CaseRun(inject, testcaseinject=testcase)
                for inject in injects
                for testcase in self._object.testcases._items
                if int(inject["case_id"]) == testcase.id])
        self._original = set(self._current)

    def _add(self, caseruns):
        """ Adding supported by CaseRun() or TestRun.testcases.add() """
        raise NitrateError(
                "Use TestRun.testcases.add([testcases]) to add new test cases")

    def _remove(self, caseruns):
        """ Removing supported by TestRun.testcases.remove() """
        raise NitrateError(
                "Use TestRun.testcases.remove([testcases]) to remove cases")

    def __iter__(self):
        """ Iterate over all included case runs ordered by sortkey """
        for caserun in sorted(self._items, key=lambda x: x.sortkey):
            yield caserun

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  RunCaseRuns Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan
            self.testrun = Nitrate()._config.testrun
            self.caserun = Nitrate()._config.caserun

        def test_present(self):
            """ Check case run presence """
            caserun = CaseRun(self.caserun.id)
            testrun = TestRun(self.testrun.id)
            self.assertTrue(caserun in testrun)

        def test_cases_fetched_just_once(self):
            """ Test cases are fetched just once """
            # This test is relevant when caching is turned on
            if _cache_level < CACHE_OBJECTS: return
            Cache.clear()
            testplan = TestPlan(self.testplan.id)
            testrun = TestRun(self.testrun.id)
            # Make sure plan, run and cases are fetched
            text = "{0}{1}{2}".format(testplan, testrun, listed(
                    [testcase for testcase in testplan]))
            # Now fetching case runs should be a single query to the
            # server because all test cases have already been fetched
            requests = Nitrate._requests
            statuses = listed([caserun.status for caserun in testrun])
            self.assertEqual(Nitrate._requests, requests + 1)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CasePlan Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CasePlan(Mutable):
    """
    Test case plan object

    Used mainly for storing different test case sortkey for different
    test plans.
    """

    # Identifier width and local cache
    _identifier_width = 12
    _cache = {}
    # List of all object attributes (used for init & expiration)
    _attributes = ["testcase", "testplan", "sortkey"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  CasePlan Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Case plan id (internal fake)")
    testcase = property(_getter("testcase"), doc="Test case object.")
    testplan = property(_getter("testplan"), doc="Test plan object.")

    # Read-write properties
    sortkey = property(_getter("sortkey"), _setter("sortkey"),
            doc="Test case plan sort key (int).")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  CasePlan Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, *args, **kwargs):
        """ Create a new object, handle caching if enabled. """
        # Parse our internal fake id if both testcase and testplan given
        id = CasePlan._fake_id(
                id, kwargs.get("testcase"), kwargs.get("testplan"))
        return super(CasePlan, cls).__new__(cls, id, *args, **kwargs)

    def __init__(self, id=None, testcase=None, testplan=None, **kwargs):
        """
        Initialize a test case plan

        Provide internal fake id or both test case and test plan.
        """
        # Prepare fake internal id if both testcase and testplan given
        id = CasePlan._fake_id(id, testcase, testplan)
        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id, **kwargs)
        if initialized: return
        Mutable.__init__(self, id, prefix="CP")
        # If inject given, fetch test case plan data from it
        if inject:
            self._fetch(inject, **kwargs)
        # Otherwise just make sure all requested parameter were given
        elif not id and (testcase is None or testplan is None):
            raise NitrateError("Need either internal id or both test case "
                    "and test plan to initialize the CasePlan object")

    def __unicode__(self):
        """ Test case, test plan and sortkey for printing """
        return u"{0} in {1} with sortkey {2}".format(
                self.testcase.identifier,
                self.testplan.identifier,
                self.sortkey)

    @staticmethod
    def _fake_id(id, testcase, testplan):
        """ Prepare internal fake id from testcase and testplan """
        # Nothing to do when id provided
        if id is not None:
            return id
        # Extract ids if objects given
        if isinstance(testcase, TestCase):
            testcase = testcase.id
        if isinstance(testplan, TestPlan):
            testplan = testplan.id
        # Idify if both testcase and testplan provided
        if testcase is not None and testplan is not None:
            return _idify([testplan, testcase])
        return None

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  CasePlan Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None, **kwargs):
        """ Initialize / refresh test case plan data """
        Nitrate._fetch(self, inject)

        # Fetch data from the server if no inject given
        if inject is None:
            log.info("Fetching case plan {0}".format(self.identifier))
            testplan, testcase = _idify(self.id)
            inject = self._server.TestCasePlan.get(testcase, testplan)
            self._inject = inject
        # Use our internal fake id instead of the server one
        self._id = _idify([inject["plan_id"], inject["case_id"]])
        log.debug("Initializing case plan {0}".format(self.identifier))
        log.xmlrpc(pretty(inject))

        # Set up attributes
        self._testcase = TestCase(inject["case_id"])
        self._testplan = TestPlan(inject["plan_id"])
        self._sortkey = inject["sortkey"]

        # Index the fetched object into cache
        self._index()

    def _update(self, proxy=None):
        """ Save test case plan data to the server """
        log.info("Updating case plan {0}".format(self.identifier))
        log.xmlrpc("{0}, {1}, {2}".format(
                self.testcase.id, self.testplan.id, self.sortkey))
        # Use custom proxy if given
        if proxy is None:
            proxy = self._multicall
        proxy.TestCasePlan.update(
                self.testcase.id, self.testplan.id, self.sortkey)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  CasePlan Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan
            self.testcase = Nitrate()._config.testcase
        def test_sortkey_update(self):
            """ Sort key update """
            testcase = self.testcase.id
            testplan = self.testplan.id
            for sortkey in [100, 200, 300]:
                # Update the sortkey
                caseplan = CasePlan(testcase=testcase, testplan=testplan)
                caseplan.sortkey = sortkey
                caseplan.update()
                self.assertEqual(caseplan.sortkey, sortkey)
                # Check the cache content
                if get_cache_level() < CACHE_OBJECTS: continue
                requests = Nitrate._requests
                caseplan = CasePlan(testcase=testcase, testplan=testplan)
                self.assertEqual(caseplan.sortkey, sortkey)
                self.assertEqual(requests, Nitrate._requests)
                # Check persistent cache
                if get_cache_level() < CACHE_PERSISTENT: continue
                Cache.save()
                Cache.clear()
                Cache.load()
                caseplan = CasePlan(testcase=testcase, testplan=testplan)
                self.assertEqual(caseplan.sortkey, sortkey)
                self.assertEqual(requests, Nitrate._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanCasePlans Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanCasePlans(Container):
    """ Test case plan objects related to a test plan """

    # Local cache & class of contained objects
    _cache = {}
    _class = CasePlan

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanCasePlans Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inset=None):
        """ Fetch case plans from the server """
        # If data initialized from the inset ---> we're done
        if Container._fetch(self, inset): return

        # Fetch test case plans from the server using multicall
        log.info("Fetching case plans for {0}".format(self._identifier))
        multicall = xmlrpclib.MultiCall(self._server)
        for testcase in self._object.testcases._items:
            multicall.TestCasePlan.get(testcase.id, self._object.id)
        injects = [inject for inject in multicall()]
        log.xmlrpc(pretty(injects))

        # And finally create the initial object set
        self._current = set([CasePlan(inject) for inject in injects])
        self._original = set(self._current)

    def _add(self, caseplans):
        """ Test case linking is handled by PlanCases class """
        # Nothing to do on our side
        pass

    def _remove(self, caseplans):
        """ Test case unlinking is handled by PlanCases class """
        # Nothing to do on our side
        pass

    def add(self, caseplans):
        """ Add case plans to the container """
        # The method is used just for sync with PlanCases, we never add
        # CasePlans to the server, thus we never get modified
        super(PlanCasePlans, self).add(caseplans)
        self._modified = False

    def remove(self, caseplans):
        """ Remove case plans from the container """
        # The method is used just for sync with PlanCases, we never remove
        # CasePlans to the server, thus we never get modified
        super(PlanCasePlans, self).remove(caseplans)
        self._modified = False

    def update(self):
        """ Update case plans with modified sortkey """
        modified = [caseplan for caseplan in self if caseplan._modified]
        # Nothing to do if there are no sortkey changes
        if not modified: return
        # Update all modified caseplans in a single multicall
        log.info("Updating {0}'s case plans".format(self._identifier))
        multicall = xmlrpclib.MultiCall(self._server)
        for caseplan in modified:
            caseplan._update(multicall)
            caseplan._modified = False
        multicall()

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanCasePlans Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan
            self.testcase = Nitrate()._config.testcase
        def test_sortkey_update(self):
            """ Get/set sortkey using the TestPlan.sortkey() method """
            testcase = TestCase(self.testcase.id)
            testplan = TestPlan(self.testplan.id)
            for sortkey in [100, 200, 300]:
                # Compare current sortkey value
                caseplan = CasePlan(testcase=testcase, testplan=testplan)
                self.assertEqual(testplan.sortkey(testcase), caseplan.sortkey)
                # Update the sortkey
                testplan.sortkey(testcase, sortkey)
                testplan.update()
                self.assertEqual(testplan.sortkey(testcase), sortkey)
                # Check the cache content
                if get_cache_level() < CACHE_OBJECTS: continue
                requests = Nitrate._requests
                testplan = TestPlan(self.testplan.id)
                self.assertEqual(testplan.sortkey(testcase), sortkey)
                self.assertEqual(requests, Nitrate._requests)
                # Check persistent cache
                if get_cache_level() < CACHE_PERSISTENT: continue
                Cache.save()
                Cache.clear()
                Cache.load()
                testplan = TestPlan(self.testplan.id)
                self.assertEqual(testplan.sortkey(testcase), sortkey)
                self.assertEqual(requests, Nitrate._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Cache Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Cache(Nitrate):
    """
    Persistent Cache

    Responsible for saving/loading all cached objects into/from local
    persistent cache saved in a file on disk.
    """

    # List of classes with persistent cache support
    _immutable = [Bug, Build, Version, Category, Component, PlanType, Product,
            Tag, User]
    _mutable = [TestCase, TestPlan, TestRun, CaseRun, CasePlan]
    _containers = [CaseBugs, CaseComponents, CasePlans, CaseRunBugs, CaseTags,
            ChildPlans, PlanCasePlans, PlanCases, PlanRuns, PlanTags, RunCases,
            RunCaseRuns, RunTags]
    _classes = _immutable + _mutable + _containers

    # File path to the cache
    _filename = None

    @staticmethod
    def setup(filename=None):
        """ Set cache filename and initialize expiration times """
        # Nothing to do when persistent caching is off
        if get_cache_level() < CACHE_PERSISTENT:
            return

        # Detect cache filename, argument first, then config
        if filename is not None:
            Cache._filename = filename
        else:
            try:
                Cache._filename = Nitrate()._config.cache.file
            except AttributeError:
                log.warn("Persistent caching off "
                        "(cache filename not found in the config)")

        # Initialize user-defined expiration times from the config
        for klass in Cache._classes + [Nitrate, Mutable, Container]:
            try:
                expiration = getattr(
                        Nitrate()._config.expiration, klass.__name__.lower())
            except AttributeError:
                continue
            # Convert from seconds, handle special values
            if isinstance(expiration, int):
                expiration = datetime.timedelta(seconds=expiration)
            elif expiration == "NEVER_EXPIRE":
                expiration = NEVER_EXPIRE
            elif expiration == "NEVER_CACHE":
                expiration = NEVER_CACHE
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
        if not Cache._filename or get_cache_level() < CACHE_PERSISTENT:
            return

        # Clear expired items and gather all caches into a single object
        Cache.expire()
        log.cache("Cache dump stats:\n" + Cache.stats().strip())
        data = {}
        for current_class in Cache._classes:
            # Put container classes into id-sleep
            if issubclass(current_class, Container):
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
        if not Cache._filename or get_cache_level() < CACHE_PERSISTENT:
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
                set_cache_level(CACHE_OBJECTS)
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
                elif (isinstance(current_object, Mutable) and
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
            for slice in sliced(modified, MULTICALL_MAX):
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

if __name__ != "__main__":
    # Setup up expiration times and load cache on module import
    Cache.setup()
    Cache.load()
    # Register callback to save the cache upon script exit
    atexit.register(Cache.save)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Self Test
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

else:
    """ Perform the module self-test if run directly. """

    # Override the server config with the testing instance
    try:
        Nitrate()._config.nitrate = Nitrate()._config.test
        print "Testing against {0}".format(Nitrate()._config.nitrate.url)
    except AttributeError:
        raise NitrateError("No test server provided in the config file")

    # Use temporary cache file for testing
    temporary_cache = tempfile.NamedTemporaryFile()
    Cache.setup(temporary_cache.name)

    # Parse options
    parser = optparse.OptionParser(
            usage="python nitrate.api [--performance] [class [...]]")
    parser.add_option("--performance",
            action="store_true",
            help="Run performance tests")
    (options, arguments) = parser.parse_args()

    # Custom test result class
    class ShortResult(unittest.TextTestResult):
        def getDescription(self, test):
            return test.shortDescription() or str(test)

    # Walk through all module classes
    import __main__
    results = {}
    for name in dir(__main__):
        object = getattr(__main__, name)
        # Pick Nitrate classes only
        if (isinstance(object, (type, types.ClassType)) and
                issubclass(object, Nitrate)):
            # Run the _test class if found & selected on command line
            test = getattr(object, "_test", None)
            if test and (object.__name__ in arguments or not arguments):
                suite = unittest.TestLoader().loadTestsFromTestCase(test)
                # Filter only performance test cases when --performance given
                suite = [case for case in suite
                        if options.performance
                        and "performance" in str(case)
                        or not options.performance
                        and "performance" not in str(case)]
                if not suite:
                    continue
                suite = unittest.TestSuite(suite)
                print header(object.__name__)
                log_level = get_log_level()
                results[object.__name__] = unittest.TextTestRunner(
                            verbosity=2, resultclass=ShortResult).run(suite)
                set_log_level(log_level)

    # Check for failed tests and give a short test summary
    failures = sum([len(result.failures) for result in results.itervalues()])
    errors = sum([len(result.errors) for result in results.itervalues()])
    testsrun = sum([result.testsRun for result in results.itervalues()])
    print header("Summary")
    print "{0} tested".format(listed(results, "class"))
    print "{0} passed".format(listed(testsrun - failures - errors, "test"))
    print "{0} failed".format(listed(failures, "test"))
    print "{0} found".format(listed(errors, "error"))
    if failures:
        print "Failures in: {0}".format(listed([name
                for name, result in results.iteritems()
                if not result.wasSuccessful()]))
    # Save cache
    Cache.save()
