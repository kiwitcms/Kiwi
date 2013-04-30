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
import time
import types
import random
import optparse
import unittest
import datetime
import xmlrpclib
import unicodedata
import ConfigParser
import logging as log
from pprint import pformat as pretty
from xmlrpc import NitrateError, NitrateKerbXmlrpc


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Logging
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_log_level = log.WARN

def set_log_level(level=None):
    """
    Set the default log level

    If the level is not specified environment variable DEBUG is used
    with the following meaning:

        DEBUG=0 ... Nitrate.log.WARN (default)
        DEBUG=1 ... Nitrate.log.INFO
        DEBUG=2 ... Nitrate.log.DEBUG
        DEBUG=3 ... Nitrate.log.NOTSET (log all messages)
    """

    global _log_level
    mapping = {
            0: log.WARN,
            1: log.INFO,
            2: log.DEBUG,
            3: log.NOTSET,
            }
    # If level specified, use given
    if level is not None:
        _log_level = level
    # Otherwise attempt to detect from the environment
    else:
        try:
            _log_level = mapping[int(os.environ["DEBUG"])]
        except StandardError:
            _log_level = log.WARN
    log.basicConfig(format="[%(levelname)s] %(message)s")
    log.getLogger().setLevel(_log_level)

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
#  Caching
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CACHE_NONE = 0
CACHE_CHANGES = 1
CACHE_OBJECTS = 2
CACHE_ALL = 3

_cache_level = CACHE_OBJECTS

def set_cache_level(level=None):
    """
    Set the caching level

    If the level parameter is not specified environment variable CACHE
    is inspected instead.  There are three levels available:

        CACHE_NONE ...... Write object changes immediately to the server
        CACHE_CHANGES ... Changes pushed only by update() or upon destruction
        CACHE_OBJECTS ... Any loaded object is saved for possible future use
        CACHE_ALL ....... Where possible, pre-fetch all available objects

    By default CACHE_OBJECTS is used. That means any changes to objects
    are pushed to the server only upon destruction or when explicitly
    requested with the update() method.  Also, any object already loaded
    from the server is kept in local cache so that future references to
    that object are faster.
    """

    global _cache_level
    if level is None:
        try:
            _cache_level = int(os.environ["CACHE"])
        except StandardError:
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
#  Coloring
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

COLOR_ON = 1
COLOR_OFF = 0
COLOR_AUTO = 2

_color_mode = COLOR_AUTO
_color = True

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

set_color_mode()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Default Getter & Setter
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _getter(field):
    """
    Simple getter factory function.

    For given field generate getter function which calls self._get(), to
    initialize instance data if necessary, and returns self._field.
    """

    def getter(self):
        # Initialize the attribute unless already done
        if getattr(self, "_" + field) is NitrateNone:
            self._get()
        # Return self._field
        return getattr(self, "_" + field)

    return getter

def _setter(field):
    """
    Simple setter factory function.

    For given field return setter function which calls self._get(), to
    initialize instance data if necessary, updates the self._field and
    remembers modifed state if the value is changed.
    """

    def setter(self, value):
        # Initialize the attribute unless already done
        if getattr(self, "_" + field) is NitrateNone:
            self._get()
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
        if singular.endswith("y"):
            plural = singular[:-1] + "ies"
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

def ascii(text):
    """ Transliterate special unicode characters into pure ascii. """
    if not isinstance(text, unicode): text = unicode(text)
    return unicodedata.normalize('NFKD', text).encode('ascii','ignore')


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
#  Nitrate Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Nitrate(object):
    """
    General Nitrate Object.

    Takes care of initiating the connection to the Nitrate server and
    parses user configuration.
    """

    _connection = None
    _settings = None
    _requests = 0

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Object identifier.")

    @property
    def identifier(self):
        """ Consistent identifier string. """
        return "{0}#{1}".format(self._prefix, self._id)

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
            log.info(u"Contacting server {0}".format(self._config.nitrate.url))
            Nitrate._connection = NitrateKerbXmlrpc(
                    self._config.nitrate.url).server

        # Return existing connection
        Nitrate._requests += 1
        return Nitrate._connection

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, prefix="ID"):
        """ Initialize the object id, prefix and internal attributes. """
        # Set up prefix and internal attributes
        self._prefix = prefix
        try:
            for attr in self._attributes:
                setattr(self, "_" + attr, NitrateNone)
        except AttributeError:
            self._attributes = []

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
        """ Handle object equality based on its id. """
        if not isinstance(other, Nitrate): return False
        return self.id == other.id

    def __ne__(self, other):
        """ Handle object inequality based on its id. """
        if not isinstance(other, Nitrate): return True
        return self.id != other.id

    def __hash__(self):
        """ Use object id as the default hash. """
        return self.id

    def __repr__(self):
        """ Provide Object(id) representation. """
        return "{0}({1})".format(self.__class__.__name__, self.id)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Fetch object data from the server. """
        raise NitrateError("To be implemented by respective class")


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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Build id.")
    name = property(_getter("name"), doc="Build name.")
    product = property(_getter("product"), doc="Relevant product.")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, product=None, build=None):
        """ Initialize by build id or product and build name. """

        # Initialized by id
        if id is not None:
            self._name = self._product = NitrateNone
        # Initialized by product and build
        elif product is not None and build is not None:
            # Detect product format
            if isinstance(product, Product):
                self._product = product
            elif isinstance(product, basestring):
                self._product = Product(name=product)
            else:
                self._product = Product(id=product)
            self._name = build
        else:
            raise NitrateError("Need either build id or both product "
                    "and build name to initialize the Build object.")
        Nitrate.__init__(self, id)

    def __unicode__(self):
        """ Build name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Get the missing build data. """

        # Search by id
        if self._id is not NitrateNone:
            try:
                log.info("Fetching build " + self.identifier)
                hash = self._server.Build.get(self.id)
                log.debug("Initializing build " + self.identifier)
                log.debug(pretty(hash))
                self._name = hash["name"]
                self._product = Product(hash["product_id"])
            except LookupError:
                raise NitrateError(
                        "Cannot find build for " + self.identifier)
        # Search by product and name
        else:
            try:
                log.info(u"Fetching build '{0}' of '{1}'".format(
                        self.name, self.product.name))
                hash = self._server.Build.check_build(
                        self.name, self.product.id)
                log.debug(u"Initializing build '{0}' of '{1}'".format(
                        self.name, self.product.name))
                log.debug(pretty(hash))
                self._id = hash["build_id"]
            except LookupError:
                raise NitrateError("Build '{0}' not found in '{1}'".format(
                    self.name, self.product.name))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Category Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Category(Nitrate):
    """ Test case category. """

    # Local cache of Category objects indexed by category id
    _categories = {}

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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, product=None, category=None):
        """ Create a new object, handle caching if enabled. """
        if _cache_level >= CACHE_OBJECTS and id is not None:
            # Search the cache
            if id in Category._categories:
                log.debug("Using cached category ID#{0}".format(id))
                return Category._categories[id]
            # Not cached yet, create a new one and cache
            else:
                log.debug("Caching category ID#{0}".format(id))
                new = Nitrate.__new__(cls)
                Category._categories[id] = new
                return new
        else:
            return Nitrate.__new__(cls)

    def __init__(self, id=None, product=None, category=None):
        """ Initialize by category id or product and category name. """

        # If we are a cached-already object no init is necessary
        if getattr(self, "_id", None) is not None:
            return

        # Initialized by id
        if id is not None:
            self._name = self._product = NitrateNone
        # Initialized by product and category
        elif product is not None and category is not None:
            # Detect product format
            if isinstance(product, Product):
                self._product = product
            elif isinstance(product, basestring):
                self._product = Product(name=product)
            else:
                self._product = Product(id=product)
            self._name = category
        else:
            raise NitrateError("Need either category id or both product "
                    "and category name to initialize the Category object.")
        Nitrate.__init__(self, id)

    def __unicode__(self):
        """ Category name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Get the missing category data. """

        # Search by id
        if self._id is not NitrateNone:
            try:
                log.info("Fetching category " + self.identifier)
                hash = self._server.Product.get_category(self.id)
                log.debug("Initializing category " + self.identifier)
                log.debug(pretty(hash))
                self._name = hash["name"]
                self._product = Product(hash["product_id"])
            except xmlrpclib.Fault:
                raise NitrateError(
                        "Cannot find category for " + self.identifier)
        # Search by product and name
        else:
            try:
                log.info(u"Fetching category '{0}' of '{1}'".format(
                        self.name, self.product.name))
                hash = self._server.Product.check_category(
                        self.name, self.product.id)
                log.debug(u"Initializing category '{0}' of '{1}'".format(
                        self.name, self.product.name))
                log.debug(pretty(hash))
                self._id = hash["id"]
            except xmlrpclib.Fault:
                raise NitrateError("Category '{0}' not found in '{1}'".format(
                    self.name, self.product.name))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):

        def setUp(self):
            """ Set up test product from the config """
            self.product = Nitrate()._config.product

        def testCachingOn(self):
            """ Category caching on """
            # Make sure the cache is empty
            Category._categories = {}
            # Enable cache, remember current number of requests
            original = get_cache_level()
            set_cache_level(CACHE_OBJECTS)
            requests = Nitrate._requests
            # The first round (fetch category data from server)
            category = Category(1)
            self.assertTrue(isinstance(category.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            del category
            # The second round (there should be no more requests)
            category = Category(1)
            self.assertTrue(isinstance(category.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            # Restore cache level
            set_cache_level(original)

        def testCachingOff(self):
            """ Category caching off """
            # Enable cache, remember current number of requests
            original = get_cache_level()
            set_cache_level(CACHE_NONE)
            requests = Nitrate._requests
            # The first round (fetch category data from server)
            category = Category(1)
            self.assertTrue(isinstance(category.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            del category
            # The second round (there should be another request)
            category = Category(1)
            self.assertTrue(isinstance(category.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 2)
            # Restore cache level
            set_cache_level(original)

        def test_invalid_category(self):
            """ Invalid category should raise exception """
            def fun():
                Category(category="Bad Category", product=self.product.name).id
            self.assertRaises(NitrateError, fun)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Type Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanType(Nitrate):
    """ Plan type """

    # Local cache of PlanType objects indexed by plan type id
    _plantypes = {}

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanType Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Test plan type id")
    name = property(_getter("name"), doc="Test plan type name")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanType Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, name=None):
        """ Create a new object, handle caching if enabled. """
        if _cache_level >= CACHE_OBJECTS and id is not None:
            # Search the cache
            if id in PlanType._plantypes:
                log.debug("Using cached plantype ID#{0}".format(id))
                return PlanType._plantypes[id]
            # Not cached yet, create a new one and cache
            else:
                log.debug("Caching plantype ID#{0}".format(id))
                new = Nitrate.__new__(cls)
                PlanType._plantypes[id] = new
                return new
        else:
            return Nitrate.__new__(cls)

    def __init__(self, id=None, name=None):
        """ Initialize by test plan type id or name """

        # If we are a cached-already object no init is necessary
        if getattr(self, "_id", None) is not None:
            return

        # Allow initialization by string e.g. PlanType("General")
        if isinstance(id, basestring):
            name = id
            id = None
        # Initialized by id
        if id is not None:
            self._name = NitrateNone
        # Initialized by name
        elif name is not None:
            self._name = name
        else:
            raise NitrateError(
                    "Need either id or name to initialize the PlanType object")
        Nitrate.__init__(self, id)

    def __unicode__(self):
        """ PlanType name for printing """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanType Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Get the missing test plan type data """

        # Search by id
        if self._id is not NitrateNone:
            try:
                log.info("Fetching test plan type " + self.identifier)
                hash = self._server.TestPlan.get_plan_type(self.id)
                log.debug("Initializing test plan type " + self.identifier)
                log.debug(pretty(hash))
                self._name = hash["name"]
            except xmlrpclib.Fault:
                raise NitrateError(
                        "Cannot find test plan type for " + self.identifier)
        # Search by name
        else:
            try:
                log.info(u"Fetching test plan type '{0}'".format(self.name))
                hash = self._server.TestPlan.check_plan_type(self.name)
                log.debug(u"Initializing test plan type '{0}'".format(
                        self.name))
                log.debug(pretty(hash))
                self._id = hash["id"]
            except xmlrpclib.Fault:
                raise NitrateError("PlanType '{0}' not found".format(
                        self.name))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanType Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up plan type from the config """
            self.plantype = Nitrate()._config.plantype

        def testCachingOn(self):
            """ PlanType caching on """
            # Make sure the cache is empty
            PlanType._plantypes = {}
            # Enable cache, remember current number of requests
            original = get_cache_level()
            set_cache_level(CACHE_OBJECTS)
            requests = Nitrate._requests
            # The first round (fetch plantype data from server)
            plantype = PlanType(1)
            self.assertTrue(isinstance(plantype.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            del plantype
            # The second round (there should be no more requests)
            plantype = PlanType(1)
            self.assertTrue(isinstance(plantype.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            # Restore cache level
            set_cache_level(original)

        def testCachingOff(self):
            """ PlanType caching off """
            # Disable cache, remember current number of requests
            original = get_cache_level()
            set_cache_level(CACHE_NONE)
            requests = Nitrate._requests
            # The first round (fetch plantype data from server)
            plantype = PlanType(1)
            self.assertTrue(isinstance(plantype.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            del plantype
            # The second round (there should be another request)
            plantype = PlanType(1)
            self.assertTrue(isinstance(plantype.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 2)
            # Restore cache level
            set_cache_level(original)

        def test_invalid_type(self):
            """ Invalid test plan type should raise exception """
            def fun():
                PlanType(name="Bad Plan Type").id
            self.assertRaises(NitrateError, fun)

        def test_valid_type(self):
            """ Valid test plan type initialization """
            # Initialize by id
            plantype = PlanType(self.plantype.id)
            self.assertEqual(plantype.name, self.plantype.name)
            # Initialize by name (explicit)
            plantype = PlanType(name=self.plantype.name)
            self.assertEqual(plantype.id, self.plantype.id)
            # Initialize by name (autodetection)
            plantype = PlanType(self.plantype.name)
            self.assertEqual(plantype.id, self.plantype.id)


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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Product id")
    name = property(_getter("name"), doc="Product name")

    # Read-write properties
    version = property(_getter("version"), _setter("version"),
            doc="Default product version")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None, version=None):
        """ Initialize the Product.

        One of id or name parameters must be provided. Optional version
        argument sets the default product version.
        """

        # Initialize by id
        if id is not None:
            self._name = NitrateNone
        # Initialize by name
        elif name is not None:
            self._name = name
            self._id = NitrateNone
        else:
            raise NitrateError("Need id or name to initialize Product")
        Nitrate.__init__(self, id)

        # Optionally initialize version
        if version is not None:
            self._version = Version(product=self, version=version)
        else:
            self._version = NitrateNone

    def __unicode__(self):
        """ Product name for printing. """
        if self._version is not NitrateNone:
            return u"{0}, version {1}".format(self.name, self.version)
        else:
            return self.name

    @staticmethod
    def search(**query):
        """ Search for products. """
        return [Product(hash["id"])
                for hash in Nitrate()._server.Product.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Fetch product data from the server. """

        # Search by id
        if self._id is not NitrateNone:
            try:
                log.info("Fetching product " + self.identifier)
                hash = self._server.Product.filter({'id': self.id})[0]
                log.debug("Initializing product " + self.identifier)
                log.debug(pretty(hash))
                self._name = hash["name"]
            except IndexError:
                raise NitrateError(
                        "Cannot find product for " + self.identifier)
        # Search by name
        else:
            try:
                log.info(u"Fetching product '{0}'".format(self.name))
                hash = self._server.Product.filter({'name': self.name})[0]
                log.debug(u"Initializing product '{0}'".format(self.name))
                log.debug(pretty(hash))
                self._id = hash["id"]
            except IndexError:
                raise NitrateError(
                        "Cannot find product for '{0}'".format(self.name))

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
    _users = {}

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="User id.")
    login = property(_getter("login"), doc="Login username.")
    email = property(_getter("email"), doc="User email address.")
    name = property(_getter("name"), doc="User first name and last name.")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, login=None, email=None, hash=None):
        """ Create a new object, handle caching if enabled. """
        id, login, email = cls._parse(id, login, email)
        # Fetch all users if in CACHE_ALL level and the cache is still empty
        if hash is None and _cache_level == CACHE_ALL and not User._users:
            log.info("Caching all users")
            for hash in Nitrate()._server.User.filter({}):
                user = User(hash=hash)
                User._users[user.id] = user
        if hash is None and _cache_level >= CACHE_OBJECTS and id is not None:
            # Search the cache
            if id in User._users:
                log.debug("Using cached user UID#{0}".format(id))
                return User._users[id]
            # Not cached yet, create a new one and cache
            else:
                log.debug("Caching user UID#{0}".format(id))
                new = Nitrate.__new__(cls)
                User._users[id] = new
                return new
        else:
            return Nitrate.__new__(cls)

    def __init__(self, id=None, login=None, email=None, hash=None):
        """ Initialize by user id, login or email.

        Defaults to the current user if no id, login or email provided.
        If xmlrpc hash provided, data are initilized directly from it.
        """
        # If we are a cached-already object no init is necessary
        if getattr(self, "_id", None) is not None:
            return

        # Initialize values
        self._name = self._login = self._email = NitrateNone
        id, login, email = self._parse(id, login, email)
        Nitrate.__init__(self, id, prefix="UID")
        if hash is not None:
            self._get(hash=hash)
        elif login is not None:
            self._login = login
        elif email is not None:
            self._email = email

    def __unicode__(self):
        """ User login for printing. """
        return self.name if self.name is not None else u"No Name"

    @staticmethod
    def search(**query):
        """ Search for users. """
        return [User(hash=hash)
                for hash in Nitrate()._server.User.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @staticmethod
    def _parse(id, login, email):
        """ Detect login & email if passed as the first parameter. """
        if isinstance(id, basestring):
            if '@' in id:
                email = id
            else:
                login = id
            id = None
        return id, login, email

    def _get(self, hash=None):
        """ Fetch user data from the server. """

        if hash is None:
            # Search by id
            if self._id is not NitrateNone:
                try:
                    log.info("Fetching user " + self.identifier)
                    hash = self._server.User.filter({"id": self.id})[0]
                except IndexError:
                    raise NitrateError(
                            "Cannot find user for " + self.identifier)
            # Search by login
            elif self._login is not NitrateNone:
                try:
                    log.info(
                            "Fetching user for login '{0}'".format(self.login))
                    hash = self._server.User.filter(
                            {"username": self.login})[0]
                except IndexError:
                    raise NitrateError("No user found for login '{0}'".format(
                            self.login))
            # Search by email
            elif self._email is not NitrateNone:
                try:
                    log.info("Fetching user for email '{0}'" + self.email)
                    hash = self._server.User.filter({"email": self.email})[0]
                except IndexError:
                    raise NitrateError("No user found for email '{0}'".format(
                            self.email))
            # Otherwise initialize to the current user
            else:
                log.info("Fetching the current user")
                hash = self._server.User.get_me()

        # Save values
        log.debug("Initializing user UID#{0}".format(hash["id"]))
        log.debug(pretty(hash))
        self._id = hash["id"]
        self._login = hash["username"]
        self._email = hash["email"]
        if hash["first_name"] and hash["last_name"]:
            self._name = hash["first_name"] + " " + hash["last_name"]
        else:
            self._name = None

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def test_no_name(self):
            """ User with no name set in preferences """
            user = User()
            user._name = None
            self.assertEqual(unicode(user), u"No Name")
            self.assertEqual(str(user), "No Name")


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Version Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Version(Nitrate):
    """ Product version. """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Version id")
    name = property(_getter("name"), doc="Version name")
    product = property(_getter("product"), doc="Relevant product")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, product=None, version=None):
        """ Initialize by version id or product and version. """

        # Initialized by id
        if id is not None:
            self._name = self._product = NitrateNone
        # Initialized by product and version
        elif product is not None and version is not None:
            # Detect product format
            if isinstance(product, Product):
                self._product = product
            elif isinstance(product, basestring):
                self._product = Product(name=product)
            else:
                self._product = Product(id=product)
            self._name = version
        else:
            raise NitrateError("Need either version id or both product "
                    "and version name to initialize the Version object.")
        Nitrate.__init__(self, id)

    def __unicode__(self):
        """ Version name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Fetch version data from the server. """

        # Search by id
        if self._id is not NitrateNone:
            try:
                log.info("Fetching version " + self.identifier)
                hash = self._server.Product.filter_versions({'id': self.id})
                log.debug("Initializing version " + self.identifier)
                log.debug(pretty(hash))
                self._name = hash[0]["value"]
                self._product = Product(hash[0]["product_id"])
            except IndexError:
                raise NitrateError(
                        "Cannot find version for " + self.identifier)
        # Search by product and name
        else:
            try:
                log.info(u"Fetching version '{0}' of '{1}'".format(
                        self.name, self.product.name))
                hash = self._server.Product.filter_versions(
                        {'product': self.product.id, 'value': self.name})
                log.debug(u"Initializing version '{0}' of '{1}'".format(
                        self.name, self.product.name))
                log.debug(pretty(hash))
                self._id = hash[0]["id"]
            except IndexError:
                raise NitrateError(
                        "Cannot find version for '{0}'".format(self.name))


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

    def __init__(self, id=None, prefix="ID"):
        """ Initially set up to unmodified state. """
        self._modified = False
        Nitrate.__init__(self, id, prefix)

    def __del__(self):
        """ Automatically update data upon destruction. """
        try:
            self.update()
        except:
            log.exception(u"Failed to update {0}".format(self))

    def _update(self):
        """ Save data to server (to be implemented by respective class) """
        raise NitrateError("Data update not implemented")

    def update(self):
        """ Update the data, if modified, to the server """
        if self._modified:
            self._update()
            self._modified = False


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Container Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Container(Mutable):
    """
    General container class for handling sets of objects.

    Provides the add() and remove() methods for adding and removing
    objects and the internal _add() and _remove() which perform the
    actual update to the server (implemented by respective class).
    """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Related object id.")

    @property
    def _items(self):
        """ Set representation containing the items. """
        if self._current is NitrateNone:
            self._get()
        return self._current

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Container Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, object):
        """ Initialize container for specified object. """
        Mutable.__init__(self, object.id)
        self._class = object.__class__
        self._identifier = object.identifier
        self._current = NitrateNone
        self._original = NitrateNone

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

    def add(self, items):
        """ Add an item or a list of items to the container. """

        # Convert to set representation
        if isinstance(items, list):
            items = set(items)
        else:
            items = set([items])

        # If there are any new items
        if items - self._items:
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

        # If there are any new items
        if items.intersection(self._items):
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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Component Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Component(Nitrate):
    """ Test case component. """

    # Local cache of Component objects indexed by component id
    _components = {}

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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Component Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, name=None, product=None, **kwargs):
        """ Create a new object, handle caching if enabled. """
        if _cache_level >= CACHE_OBJECTS and id is not None:
            # Search the cache
            if id in Component._components:
                log.debug("Using cached component ID#{0}".format(id))
                return Component._components[id]
            # Not cached yet, create a new one and cache
            else:
                log.debug("Caching component ID#{0}".format(id))
                new = Nitrate.__new__(cls)
                Component._components[id] = new
                return new
        else:
            return Nitrate.__new__(cls)

    def __init__(self, id=None, name=None, product=None, **kwargs):
        """ Initialize by component id or product and component name. """

        # If we are a cached-already object no init is necessary
        if getattr(self, "_id", None) is not None:
            return

        # Prepare attributes, check component hash, initialize
        self._attributes = ["name", "product"]
        componenthash = kwargs.get("componenthash")
        if componenthash:
            id = componenthash["id"]
        Nitrate.__init__(self, id)

        # If hash provided, let's initialize the data immediately
        if componenthash:
            self._get(componenthash=componenthash)
        # Initialized by product and component
        elif product and name:
            # Detect product format
            if isinstance(product, Product):
                self._product = product
            elif isinstance(product, basestring):
                self._product = Product(name=product)
            else:
                self._product = Product(id=product)
            self._name = name
        # Otherwise the id must provided
        elif id is None:
            raise NitrateError("Need either component id or both product "
                    "and component name to initialize the Component object.")

    def __unicode__(self):
        """ Component name for printing. """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Component Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self, componenthash=None):
        """ Get the missing component data. """

        # Search by component id or use prepared component hash
        if self._id is not NitrateNone:
            try:
                if not componenthash:
                    log.info("Fetching component " + self.identifier)
                    componenthash = self._server.Product.get_component(self.id)
                log.debug("Initializing component " + self.identifier)
                log.debug(pretty(componenthash))
                self._name = componenthash["name"]
                self._product = Product(componenthash["product_id"])
            except LookupError:
                raise NitrateError(
                        "Cannot find component for " + self.identifier)
        # Search by product and component name
        else:
            try:
                log.info(u"Fetching component '{0}' of '{1}'".format(
                        self.name, self.product.name))
                componenthash = self._server.Product.check_component(
                        self.name, self.product.id)
                log.debug(u"Initializing component '{0}' of '{1}'".format(
                        self.name, self.product.name))
                log.debug(pretty(componenthash))
                self._id = componenthash["id"]
            except LookupError:
                raise NitrateError("Component '{0}' not found in '{1}'".format(
                    self.name, self.product.name))

    @staticmethod
    def search(**query):
        """ Search for components. """
        return [Component(componenthash=hash) for hash in
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
            Component._components = {}
            # Enable cache, remember current number of requests
            original = get_cache_level()
            set_cache_level(CACHE_OBJECTS)
            requests = Nitrate._requests
            # The first round (fetch component data from server)
            component = Component(self.component.id)
            self.assertTrue(isinstance(component.name, basestring))
            self.assertEqual(Nitrate._requests, requests + 1)
            del component
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

    def _get(self):
        """ Fetch currently linked components from the server. """
        log.info("Fetching {0}'s components".format(self._identifier))
        self._current = set([Component(componenthash=hash)
                for hash in self._server.TestCase.get_components(self.id)])
        self._original = set(self._current)

    def _add(self, components):
        """ Link provided components to the test case. """
        log.info(u"Linking {1} to {0}".format(self._identifier,
                    listed([component.name for component in components])))
        self._server.TestCase.add_component(
                self.id, [component.id for component in components])

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

        def testLinkComponent1(self):
            """ Linking a component to a test case """
            testcase = TestCase(self.testcase.id)
            component = Component(self.component.id)
            testcase.components.add(component)
            testcase.update()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component in testcase.components)

        def testLinkComponent2(self):
            """ Unlinking a component from a test case """
            testcase = TestCase(self.testcase.id)
            component = Component(self.component.id)
            testcase.components.remove(component)
            testcase.update()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component not in testcase.components)

        def testLinkComponent3(self):
            """ Linking a component to a test case """
            testcase = TestCase(self.testcase.id)
            component = Component(self.component.id)
            testcase.components.add(component)
            testcase.update()
            testcase = TestCase(self.testcase.id)
            self.assertTrue(component in testcase.components)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Bug Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Bug(Nitrate):
    """ Bug related to a test case or a case run. """

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
        """ Short summary about the bug. """
        # Summary in the form: BUG#123456 (BZ#123, TC#456, CR#789)
        return "{0} ({1})".format(self.identifier, ", ".join([str(self)] +
                [obj.identifier for obj in (self.testcase, self.caserun)
                if obj is not None]))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bug Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, bug=None, system=1, testcase=None, caserun=None,
            hash=None):
        """
        Initialize the bug.

        Provide external bug id, optionally bug system (Bugzilla by default)
        and related testcase and/or caserun object or provide complete hash.
        """

        # Initialize id & values
        if bug is not None:
            self._bug = bug
            self._system = system
            self._testcase = testcase
            self._caserun = caserun
            Nitrate.__init__(self, 0, prefix="BUG")
            self._id = "UNKNOWN"
        else:
            self._bug = int(hash["bug_id"])
            self._system = int(hash["bug_system_id"])
            self._testcase = self._caserun = None
            if hash["case_id"] is not None:
                self._testcase = TestCase(hash["case_id"])
            if hash["case_run_id"] is not None:
                self._caserun = CaseRun(hash["case_run_id"])
            Nitrate.__init__(self, hash["id"], prefix="BUG")

    def __eq__(self, other):
        """ Custom bug comparation.

        Primarily decided by id. If not set, compares by bug id, bug system,
        related testcase and caserun.
        """
        if self.id != "UNKNOWN" and other.id != "UNKNOWN":
            return self.id == other.id
        return (
                # Bug, system and case run must be equal
                self.bug == other.bug and
                self.system == other.system and
                self.caserun == other.caserun and
                # And either both case runs are defined
                (self.caserun is not None and other.caserun is not None
                # Or test cases are identical
                or self.testcase == other.testcase))

    def __unicode__(self):
        """ Bug name for printing. """
        return u"BZ#{0}".format(self.bug)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bug Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Fetch bug info from the server. """
        # No direct xmlrpc function for fetching so far
        pass

    def attach(self, object):
        """ Attach bug to the provided test case / case run object. """
        if isinstance(object, TestCase):
            return Bug(bug=self.bug, system=self.system, testcase=object)
        elif isinstance(object, CaseRun):
            return Bug(bug=self.bug, system=self.system, caserun=object)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Bugs Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Bugs(Mutable):
    """ Relevant bug list for test case and case run objects. """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bugs Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Related object id.")

    @property
    def _bugs(self):
        """ Actual list of bug objects. """
        if self._current is NitrateNone:
            self._get()
        return self._current

    @property
    def synopsis(self):
        """ Short summary about object's bugs. """
        return "{0}'s bugs: {1}".format(self._object.identifier,
                str(self) or "[NoBugs]")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bugs Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, object):
        """ Initialize bugs for specified object. """
        Mutable.__init__(self, object.id)
        self._object = object
        self._current = NitrateNone

    def __iter__(self):
        """ Bug iterator. """
        for bug in self._bugs:
            yield bug

    def __contains__(self, bug):
        """ Custom 'in' operator. """
        bug = bug.attach(self._object)
        return bug in self._bugs

    def __unicode__(self):
        """ Display bugs as list for printing. """
        return ", ".join(sorted([str(bug) for bug in self]))

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bugs Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add(self, bug):
        """ Add a bug, unless already attached. """
        # Nothing to do if already attached
        bug = bug.attach(self._object)
        if bug in self:
            log.info("{0} already attached to {1}, doing nothing".format(
                    bug, self._object.identifier))
        # Attach the bug
        else:
            log.info(u"Attaching bug {0} to {1}".format(
                    bug, self._object.identifier))
            hash = {"bug_id": bug.bug, "bug_system_id": bug.system}
            if isinstance(self._object, TestCase):
                hash["case_id"] = self.id
                log.debug(pretty(hash))
                self._server.TestCase.attach_bug(hash)
            elif isinstance(self._object, CaseRun):
                hash["case_run_id"] = self.id
                log.debug(pretty(hash))
                self._server.TestCaseRun.attach_bug(hash)
            # Append the bug to the list
            self._current.append(bug)

    def remove(self, bug):
        """ Remove a bug, if already attached. """
        # Nothing to do if not attached
        bug = bug.attach(self._object)
        if bug not in self:
            log.info(u"{0} not attached to {1}, doing nothing".format(
                    bug, self._object.identifier))
        # Detach the bug
        else:
            # Fetch the complete bug object (including the internal id)
            bug = [bugg for bugg in self if bugg == bug][0]
            log.info(u"Detaching {0}".format(self.synopsis))
            if isinstance(self._object, TestCase):
                self._server.TestCase.detach_bug(self.id, bug.id)
            elif isinstance(self._object, CaseRun):
                self._server.TestCaseRun.detach_bug(self.id, bug.id)
            # Remove the bug from the list
            self._current = [bugg for bugg in self if bugg != bug]

    def _get(self):
        """ Initialize / refresh bugs from the server. """
        log.info("Fetching bugs for {0}".format(self._object.identifier))
        # Use the respective XMLRPC call to get the bugs
        if isinstance(self._object, TestCase):
            hash = self._server.TestCase.get_bugs(self.id)
        elif isinstance(self._object, CaseRun):
            hash = self._server.TestCaseRun.get_bugs(self.id)
        else:
            raise NitrateError("No bug support for {0}".format(
                    self._object.__class__))
        log.debug(pretty(hash))

        # Save as a Bug object list
        self._current = [Bug(hash=bug) for bug in hash]

    def _update(self):
        """ Save bug changes to the server. """
        # Currently no caching for bugs, changes applied immediately
        pass


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanTags(Container):
    """ Test plan tags. """

    def _get(self):
        """ Fetch currently attached tags from the server. """
        log.info("Fetching tags for {0}".format(self._identifier))
        hash = self._server.TestPlan.get_tags(self.id)
        log.debug(pretty(hash))
        self._current = set([tag["name"] for tag in hash])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test plan. """
        log.info(u"Tagging {0} with {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestPlan.add_tag(self.id, list(tags))

    def _remove(self, tags):
        """ Detach provided tags from the test plan. """
        log.info(u"Untagging {0} of {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestPlan.remove_tag(self.id, list(tags))

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
            testplan.tags.remove("TestTag")
            testplan.update()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue("TestTag" not in testplan.tags)

        def testTagging2(self):
            """ Tagging a test plan """
            # Add tag and check
            testplan = TestPlan(self.testplan.id)
            testplan.tags.add("TestTag")
            testplan.update()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue("TestTag" in testplan.tags)

        def testTagging3(self):
            """ Untagging a test plan """
            # Remove tag and check
            testplan = TestPlan(self.testplan.id)
            testplan.tags.remove("TestTag")
            testplan.update()
            testplan = TestPlan(self.testplan.id)
            self.assertTrue("TestTag" not in testplan.tags)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Run Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunTags(Container):
    """ Test run tags. """

    def _get(self):
        """ Fetch currently attached tags from the server. """
        log.info("Fetching tags for {0}".format(self._identifier))
        hash = self._server.TestRun.get_tags(self.id)
        log.debug(pretty(hash))
        self._current = set([tag["name"] for tag in hash])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test run. """
        log.info(u"Tagging {0} with {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestRun.add_tag(self.id, list(tags))

    def _remove(self, tags):
        """ Detach provided tags from the test run. """
        log.info(u"Untagging {0} of {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestRun.remove_tag(self.id, list(tags))

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
            testrun.tags.remove("TestTag")
            testrun.update()
            testrun = TestRun(self.testrun.id)
            self.assertTrue("TestTag" not in testrun.tags)

        def testTagging2(self):
            """ Tagging a test run """
            # Add tag and check
            testrun = TestRun(self.testrun.id)
            testrun.tags.add("TestTag")
            testrun.update()
            testrun = TestRun(self.testrun.id)
            self.assertTrue("TestTag" in testrun.tags)

        def testTagging3(self):
            """ Untagging a test run """
            # Remove tag and check
            testrun = TestRun(self.testrun.id)
            testrun.tags.remove("TestTag")
            testrun.update()
            testrun = TestRun(self.testrun.id)
            self.assertTrue("TestTag" not in testrun.tags)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Case Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseTags(Container):
    """ Test case tags. """

    def _get(self):
        """ Fetch currently attached tags from the server. """
        log.info("Fetching tags for {0}".format(self._identifier))
        hash = self._server.TestCase.get_tags(self.id)
        log.debug(pretty(hash))
        self._current = set([tag["name"] for tag in hash])
        self._original = set(self._current)

    def _add(self, tags):
        """ Attach provided tags to the test case. """
        log.info(u"Tagging {0} with {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestCase.add_tag(self.id, list(tags))

    def _remove(self, tags):
        """ Detach provided tags from the test case. """
        log.info(u"Untagging {0} of {1}".format(
                self._identifier, listed(tags, quote="'")))
        self._server.TestCase.remove_tag(self.id, list(tags))

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
            testcase.tags.remove("TestTag")
            testcase.update()
            testcase = TestCase(self.testcase.id)
            self.assertTrue("TestTag" not in testcase.tags)

        def testTagging2(self):
            """ Tagging a test case """
            # Add tag and check
            testcase = TestCase(self.testcase.id)
            testcase.tags.add("TestTag")
            testcase.update()
            testcase = TestCase(self.testcase.id)
            self.assertTrue("TestTag" in testcase.tags)

        def testTagging3(self):
            """ Untagging a test case """
            # Remove tag and check
            testcase = TestCase(self.testcase.id)
            testcase.tags.remove("TestTag")
            testcase.update()
            testcase = TestCase(self.testcase.id)
            self.assertTrue("TestTag" not in testcase.tags)

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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Plan Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"),
            doc="Test plan id.")
    author = property(_getter("author"),
            doc="Test plan author.")
    tags = property(_getter("tags"),
            doc="Attached tags.")
    testcases = property(_getter("testcases"),
            doc="Test cases linked to this plan.")

    # Read-write properties
    name = property(_getter("name"), _setter("name"),
            doc="Test plan name.")
    parent = property(_getter("parent"), _setter("parent"),
            doc="Parent test plan.")
    children = property(_getter("children"), _setter("children"),
            doc="Child test plans.")
    product = property(_getter("product"), _setter("product"),
            doc="Test plan product.")
    type = property(_getter("type"), _setter("type"),
            doc="Test plan type.")
    status = property(_getter("status"), _setter("status"),
            doc="Test plan status.")

    @property
    def testruns(self):
        """ List of TestRun() objects related to this plan. """
        if self._testruns is NitrateNone:
            self._testruns = [TestRun(testrunhash=hash) for hash in
                    self._server.TestPlan.get_test_runs(self.id)]
        return self._testruns

    @property
    def synopsis(self):
        """ One line test plan overview. """
        return "{0} - {1} ({2} cases, {3} runs)".format(self.identifier,
                self.name, len(self.testcases), len(self.testruns))


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

        """

        # Prepare attributes, check test plan hash, initialize
        self._attributes = """author children name parent product status tags
                testcases testruns type""".split()
        testplanhash = kwargs.get("testplanhash")
        if testplanhash:
            id = testplanhash["plan_id"]
        Mutable.__init__(self, id, prefix="TP")

        # If hash provided, let's initialize the data immediately
        if testplanhash:
            self._get(testplanhash=testplanhash)
        # Create a new test plan if name, type and product provided
        elif name and type and product:
            self._create(name=name, product=product, version=version,
                    type=type, **kwargs)
        # Otherwise the id must be provided
        elif not id:
            raise NitrateError("Need either id or name, product, version "
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
        return [TestPlan(testplanhash=hash)
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

        # Product and Version
        if product is None:
            raise NitrateError("Product required for creating new test plan")
        elif isinstance(product, basestring):
            product = Product(name=product, version=version)
        hash["product"] = product.id

        if version is None:
            raise NitrateError("Version required for creating new test plan")
        hash["default_product_version"] = product.version.id

        # Type
        if type is None:
            raise NitrateError("Type required for creating new test plan")
        elif isinstance(type, basestring):
            type = PlanType(name=type)
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
        log.debug(pretty(hash))
        testplanhash = self._server.TestPlan.create(hash)
        log.debug(pretty(testplanhash))
        try:
            self._id = testplanhash["plan_id"]
        except TypeError:
            log.error("Failed to create a new test plan")
            log.error(pretty(hash))
            log.error(pretty(testplanhash))
            raise NitrateError("Failed to create test plan")
        self._get(testplanhash=testplanhash)
        log.info(u"Successfully created {0}".format(self))

    def _get(self, testplanhash=None):
        """ Initialize / refresh test plan data.

        Either fetch them from the server or use provided hash.
        """

        # Fetch the data hash from the server unless provided
        if testplanhash is None:
            log.info("Fetching test plan " + self.identifier)
            testplanhash = self._server.TestPlan.get(self.id)
        log.debug("Initializing test plan " + self.identifier)
        log.debug(pretty(testplanhash))
        if not "plan_id" in testplanhash:
            log.error(pretty(testplanhash))
            raise NitrateError("Failed to initialize " + self.identifier)

        # Set up attributes
        self._author = User(testplanhash["author_id"])
        self._name = testplanhash["name"]
        self._product = Product(id=testplanhash["product_id"],
                version=testplanhash["default_product_version"])
        self._type = PlanType(testplanhash["type_id"])
        self._status = PlanStatus(testplanhash["is_active"] in ["True", True])
        if testplanhash["parent_id"] is not None:
            self._parent = TestPlan(testplanhash["parent_id"])
        else:
            self._parent = None

        # Initialize containers
        self._tags = PlanTags(self)
        self._testcases = TestCases(self)
        self._children = ChildPlans(self)

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
        hash["default_product_version"] = self.product.version.id

        log.info("Updating test plan " + self.identifier)
        log.debug(pretty(hash))
        self._server.TestPlan.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._tags is not NitrateNone:
            self.tags.update()
        if self._testcases is not NitrateNone:
            self.testcases.update()
        if self._children is not NitrateNone:
            self.children.update()

        # Update self (if modified)
        Mutable.update(self)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Plan Self Test
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    class _test(unittest.TestCase):
        def setUp(self):
            """ Set up test plan from the config """
            self.testplan = Nitrate()._config.testplan

        def testCreateInvalid(self):
            """ Create a new test plan (missing required parameters) """
            self.assertRaises(NitrateError, TestPlan, name="Test plan")

        def testCreateValid(self):
            """ Create a new test plan (valid) """
            testplan = TestPlan(name="Test plan", type=self.testplan.type,
                    product=self.testplan.product,
                    version=self.testplan.version)
            self.assertTrue(isinstance(testplan, TestPlan))
            self.assertEqual(testplan.name, "Test plan")

        def testGetById(self):
            """ Fetch an existing test plan by id """
            testplan = TestPlan(self.testplan.id)
            self.assertTrue(isinstance(testplan, TestPlan))
            self.assertEqual(testplan.name, self.testplan.name)
            self.assertEqual(testplan.type.name, self.testplan.type)
            self.assertEqual(testplan.product.name, self.testplan.product)

        def testStatus(self):
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
            # XXX Disabled because of BZ#740558
            #self.assertEqual(testplan.status, negated)
            testplan.status = original
            testplan.update()
            del testplan
            # Back to the original value
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.status, original)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Test Plans Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestPlans(Container):
    """ Test plans linked to a test case. """

    def _get(self):
        """ Fetch currently linked test plans from the server. """
        log.info("Fetching {0}'s plans".format(self._identifier))
        self._current = set([TestPlan(testplanhash=hash)
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
    def caseruns(self):
        """ List of CaseRun() objects related to this run. """
        if self._caseruns is NitrateNone:
            # Fetch both test cases & test case runs
            log.info("Fetching {0}'s test cases".format(self.identifier))
            testcases = self._server.TestRun.get_test_cases(self.id)
            log.info("Fetching {0}'s case runs".format(self.identifier))
            caseruns = self._server.TestRun.get_test_case_runs(self.id)
            # Create the CaseRun objects
            self._caseruns = [
                    CaseRun(testcasehash=testcase, caserunhash=caserun)
                    for caserun in caseruns for testcase in testcases
                    if int(testcase["case_id"]) == int(caserun["case_id"])]
        return self._caseruns

    @property
    def synopsis(self):
        """ One-line test run overview. """
        return "{0} - {1} ({2} cases)".format(
                self.identifier, self.summary, len(self.caseruns))

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

        # Prepare attributes, check test run hash, initialize
        self._attributes = """build caseruns errata manager notes product
                status summary tags tester testplan time """.split()
        testrunhash = kwargs.get("testrunhash")
        if testrunhash:
            id = testrunhash["run_id"]
        Mutable.__init__(self, id, prefix="TR")

        # If hash provided, let's initialize the data immediately
        if testrunhash:
            self._get(testrunhash=testrunhash)
        # Create a new test run based on provided plan
        elif testplan:
            self._create(testplan=testplan, **kwargs)
        # Otherwise the id must be provided
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
        return [TestRun(testrunhash=hash)
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
        elif isinstance(product, basestring):
            product = Product(name=product, version=version)
        hash["product"] = product.id
        hash["product_version"] = product.version.id

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
        log.debug(pretty(hash))
        testrunhash = self._server.TestRun.create(hash)
        log.debug(pretty(testrunhash))
        try:
            self._id = testrunhash["run_id"]
        except TypeError:
            log.error(u"Failed to create a new test run based on {0}".format(
                    testplan))
            log.error(pretty(hash))
            log.error(pretty(testrunhash))
            raise NitrateError("Failed to create test run")
        self._get(testrunhash=testrunhash)
        log.info(u"Successfully created {0}".format(self))

    def _get(self, testrunhash=None):
        """ Initialize / refresh test run data.

        Either fetch them from the server or use the provided hash.
        """

        # Fetch the data hash from the server unless provided
        if testrunhash is None:
            log.info("Fetching test run " + self.identifier)
            testrunhash = self._server.TestRun.get(self.id)
        log.debug("Initializing test run " + self.identifier)
        log.debug(pretty(testrunhash))

        # Set up attributes
        self._build = Build(testrunhash["build_id"])
        self._manager = User(testrunhash["manager_id"])
        self._notes = testrunhash["notes"]
        self._status = RunStatus(testrunhash["stop_date"])
        self._summary = testrunhash["summary"]
        self._tester = User(testrunhash["default_tester_id"])
        self._testplan = TestPlan(testrunhash["plan_id"])
        self._time = testrunhash["estimated_time"]
        self._errata = testrunhash["errata_id"]

        # Initialize containers
        self._tags = RunTags(self)

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
        log.debug(pretty(hash))
        self._server.TestRun.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._tags is not NitrateNone:
            self.tags.update()

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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"),
            doc="Test case id (read-only).")
    author = property(_getter("author"),
            doc="Test case author.")
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
    product = property(_getter("product"), _setter("product"),
            doc="Test case product.")
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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, summary=None, category=None, product=None,
            **kwargs):
        """ Initialize a test case or create a new one.

        Initialize an existing test case (if id provided) or create a
        new one (based on provided summary, category and product. Other
        optional parameters supported are:

            automated ...... automation flag (default: True)
            autoproposed ... proposed for automation (default: False)
            manual ......... manual flag (default: False)
            priority ....... priority object, id or name (default: P3)
            script ......... test path (default: None)
            tester ......... user object or login (default: None)
            link ........... reference link
        """

        # Prepare attributes, check test case hash, initialize
        self._attributes = """arguments author automated autoproposed bugs
                category components link manual notes plans priority product
                script sortkey status summary tags tester testplans
                time""".split()
        testcasehash = kwargs.get("testcasehash")
        if testcasehash:
            id = testcasehash["case_id"]
        Mutable.__init__(self, id, prefix="TC")

        # If hash provided, let's initialize the data immediately
        if testcasehash:
            self._get(testcasehash=testcasehash)
        # Create a new test case based on summary, category & product
        elif summary and category and product:
            self._create(summary=summary, category=category, product=product,
                    **kwargs)
        # Otherwise the id must be provided
        elif not id:
            raise NitrateError("Need either id or summary, category "
                    "and product to initialize the test case")

    def __unicode__(self):
        """ Test case id & summary for printing. """
        return u"{0} - {1}".format(self.identifier.ljust(9), self.summary)

    @staticmethod
    def search(**query):
        """ Search for test cases. """
        return [TestCase(testcasehash=hash)
                for hash in Nitrate()._server.TestCase.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, summary, category, product, **kwargs):
        """ Create a new test case. """

        hash = {}

        # Summary
        hash["summary"] = summary

        # Product
        if isinstance(product, basestring):
            product = Product(name=product)
        hash["product"] = product.id

        # Category
        if isinstance(category, basestring):
            category = Category(category=category, product=product)
        hash["category"] = category.id

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

        # Script & reference link
        hash["script"] = kwargs.get("script")
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
        log.debug(pretty(hash))
        testcasehash = self._server.TestCase.create(hash)
        log.debug(pretty(testcasehash))
        try:
            self._id = testcasehash["case_id"]
        except TypeError:
            log.error("Failed to create a new test case")
            log.error(pretty(hash))
            log.error(pretty(testcasehash))
            raise NitrateError("Failed to create test case")
        self._get(testcasehash=testcasehash)
        log.info(u"Successfully created {0}".format(self))


    def _get(self, testcasehash=None):
        """ Initialize / refresh test case data.

        Either fetch them from the server or use provided hash.
        """

        # Fetch the data hash from the server unless provided
        if testcasehash is None:
            log.info("Fetching test case " + self.identifier)
            testcasehash = self._server.TestCase.get(self.id)
        log.debug("Initializing test case " + self.identifier)
        log.debug(pretty(testcasehash))

        # Set up attributes
        self._arguments = testcasehash["arguments"]
        self._author = User(testcasehash["author_id"])
        self._category = Category(testcasehash["category_id"])
        self._link = testcasehash["extra_link"]
        self._notes = testcasehash["notes"]
        self._priority = Priority(testcasehash["priority_id"])
        self._requirement = testcasehash["requirement"]
        self._script = testcasehash["script"]
        # XXX self._sortkey = testcasehash["sortkey"]
        self._status = CaseStatus(testcasehash["case_status_id"])
        self._summary = testcasehash["summary"]
        self._time = testcasehash["estimated_time"]
        if testcasehash["default_tester_id"] is not None:
            self._tester = User(testcasehash["default_tester_id"])
        else:
            self._tester = None

        # Handle manual, automated and autoproposed
        self._automated = testcasehash["is_automated"] in [1, 2]
        self._manual = testcasehash["is_automated"] in [0, 2]
        self._autoproposed = testcasehash["is_automated_proposed"]

        # Empty script or arguments to be handled same as None
        if self._script == "":
            self._script = None
        if self._arguments == "":
            self._arguments = None

        # Initialize containers
        self._bugs = Bugs(self)
        self._tags = CaseTags(self)
        self._testplans = TestPlans(self)
        self._components = CaseComponents(self)

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
        log.debug(pretty(hash))
        self._server.TestCase.update(self.id, hash)

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
                    link="http://example.com/test-case-link")
            self.assertTrue(
                    isinstance(case, TestCase), "Check created instance")
            self.assertEqual(case.summary, "High-priority automated test case")
            self.assertEqual(case.script, "/path/to/test/script")
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

        def testGetByStringId(self):
            """ Fetch an existing test case by id (provided as string) """
            testcase = TestCase(str(self.testcase.id))
            self.assertTrue(testcase.id, int)
            self.assertTrue(isinstance(testcase, TestCase))
            self.assertEqual(testcase.summary, self.testcase.summary)
            self.assertEqual(testcase.category.name, self.testcase.category)

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

class TestCases(Container):
    """ Test cases linked to a test plan. """

    def _get(self):
        """ Fetch currently linked test cases from the server. """
        log.info("Fetching {0}'s cases".format(self._identifier))
        try:
            self._current = set([TestCase(testcasehash=hash) for hash in
                    self._server.TestPlan.get_test_cases(self.id)])
        # Work around BZ#725726 (attempt to fetch test cases by ids)
        except xmlrpclib.Fault:
            log.warning("Failed to fetch {0}'s cases, "
                    "trying again using ids".format(self._identifier))
            self._current = set([TestCase(id) for id in
                    self._server.TestPlan.get(self.id)["case"]])
        self._original = set(self._current)

    def _add(self, cases):
        """ Link provided cases to the test plan. """
        log.info("Linking {1} to {0}".format(self._identifier,
                    listed([case.identifier for case in cases])))
        self._server.TestCase.link_plan([case.id for case in cases], self.id)

    def _remove(self, cases):
        """ Unlink provided cases from the test plan. """
        for case in cases:
            log.info("Unlinking {0} from {1}".format(
                    case.identifier, self._identifier))
            self._server.TestCase.unlink_plan(case.id, self.id)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Child Plans
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ChildPlans(Container):
    """ Child test plans of a parent plan """

    def _get(self):
        """ Find all child test plans """
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
                    product=parent.product, version=parent.product.version)
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

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Run Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, testcase=None, testrun=None, **kwargs):
        """ Initialize a test case run or create a new one.

        Initialize an existing test case run (if id provided) or create
        a new test case run (based on provided test case and test run).
        """

        # Prepare attributes, check data hashes, initialize
        self._attributes = """assignee bugs build notes sortkey status
                testcase testrun""".split()
        caserunhash = kwargs.get("caserunhash", None)
        testcasehash = kwargs.get("testcasehash", None)
        if caserunhash:
            id = caserunhash["case_run_id"]
        Mutable.__init__(self, id, prefix="CR")

        # If hashes provided, let's initialize the data immediately
        if caserunhash and testcasehash:
            self._get(caserunhash=caserunhash, testcasehash=testcasehash)
        # Create a new test case run based on case and run
        elif testcase and testrun:
            self._create(testcase=testcase, testrun=testrun, **kwargs)
        # Otherwise the id must be provided
        elif not id:
            raise NitrateError("Need either id or testcase, testrun and build "
                    "to initialize the case run")

    def __unicode__(self):
        """ Case run id, status & summary for printing. """
        return u"{0} - {1} - {2}".format(self.status.shortname,
                self.identifier.ljust(9), self.testcase.summary)

    @staticmethod
    def search(**query):
        """ Search for case runs. """
        return [CaseRun(caserunhash=hash)
                for hash in Nitrate()._server.TestCaseRun.filter(dict(query))]

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
        log.debug(pretty(hash))
        caserunhash = self._server.TestCaseRun.create(hash)
        log.debug(pretty(caserunhash))
        try:
            self._id = caserunhash["case_run_id"]
        except TypeError:
            log.error("Failed to create new case run")
            log.error(pretty(hash))
            log.error(pretty(caserunhash))
            raise NitrateError("Failed to create case run")
        self._get(caserunhash=caserunhash)
        log.info(u"Successfully created {0}".format(self))


    def _get(self, caserunhash=None, testcasehash=None):
        """ Initialize / refresh test case run data.

        Either fetch them from the server or use the supplied hashes.
        """

        # Fetch the data hash from the server unless provided
        if caserunhash is None:
            log.info("Fetching case run " + self.identifier)
            caserunhash = self._server.TestCaseRun.get(self.id)
        log.debug("Initializing case run " + self.identifier)
        log.debug(pretty(caserunhash))

        # Set up attributes
        self._assignee = User(caserunhash["assignee_id"])
        self._build = Build(caserunhash["build_id"])
        self._notes = caserunhash["notes"]
        if caserunhash["sortkey"] is not None:
            self._sortkey = int(caserunhash["sortkey"])
        else:
            self._sortkey = None
        self._status = Status(caserunhash["case_run_status_id"])
        self._testrun = TestRun(caserunhash["run_id"])
        if testcasehash:
            self._testcase = TestCase(testcasehash=testcasehash)
        else:
            self._testcase = TestCase(caserunhash["case_id"])

        # Initialize containers
        self._bugs = Bugs(self)

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
        log.debug(pretty(hash))
        self._server.TestCaseRun.update(self.id, hash)

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
            """ Updating multiple CaseRuns from a TestRun

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
#  Self Test
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    """ Perform the module self-test if run directly. """

    # Override the server url with the testing instance
    try:
        Nitrate()._config.nitrate.url = Nitrate()._config.test.url
        print "Testing against {0}".format(Nitrate()._config.nitrate.url)
    except AttributeError:
        raise NitrateError("No test server provided in the config file")

    # Parse options
    parser = optparse.OptionParser(
            usage="python nitrate.api [--performance] [class [...]]")
    parser.add_option("--performance",
            action="store_true",
            help="Run performance tests")
    (options, arguments) = parser.parse_args()

    # Walk through all module classes
    import __main__
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
                        if "performance" in str(case)
                        or not options.performance]
                if not suite:
                    continue
                suite = unittest.TestSuite(suite)
                print "\n{0}\n{1}".format(object.__name__, 70 * "~")
                unittest.TextTestRunner(verbosity=2).run(suite)
