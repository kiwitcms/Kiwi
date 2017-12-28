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
Configuration, logging, coloring & caching

To be able to contact the TCMS server a minimal user configuration
file ~/.tcms.conf has to be provided in the user home directory:

    [tcms]
    url = https://tcms.server/xml-rpc/

In that case Kerberos will be used for authentication. If username and
password are provided plain authentication will be used instead. E.g.

    [tcms]
    url = https://tcms.server/xml-rpc/
    username = login
    password = secret

It's also possible to provide system-wide config in /etc/tcms.conf.


Logging
~~~~~~~~

Standard log methods from the python 'logging' module are available
under the short name 'log'. In addition special levels have been
added for logging xmlrpc communication:

    log.error(msg) .... fatal issues which prevent task completion
    log.warn(msg) ..... non-fatal problems, not blocking execution
    log.info(msg) ..... high-level info, useful for progress tracking
    log.debug(msg) .... low-level details useful for investigation
    log.cache(msg) .... cache-related stuff and object initialization
    log.data(msg) ..... data sent to/from the xmlrpc server
    log.all(msg) ...... any other possibly useful debugging details

By default, messages of level WARN and up are only displayed. This can
be controlled by setting the current log level. See set_log_level() for
more details. In addition, you can easily display info messages using:

    info(message)

which prints provided message (to the standard error output) always,
regardless the current log level. To get a brief overview about current
status use 'print TCMS()' which gives a short summary like this:

    TCMS server: https://tcms.server/xml-rpc/
    Total requests handled: 0
"""

from configparser import ConfigParser

import datetime
import logging
import sys
import os

from tcms_api.xmlrpc import TCMSError
from tcms_api.utils import color

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Constants
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Logging
LOG_ERROR = logging.ERROR
LOG_WARN = logging.WARN
LOG_INFO = logging.INFO
LOG_DEBUG = logging.DEBUG
LOG_CACHE = 7
LOG_DATA = 4
LOG_ALL = 1

# Coloring
COLOR_ON = 1
COLOR_OFF = 0
COLOR_AUTO = 2

# Caching
NEVER_CACHE = datetime.timedelta(seconds=0)
NEVER_EXPIRE = datetime.timedelta(days=365)
CACHE_NONE = 0
CACHE_OBJECTS = 1

# Maximum id value (used for idifying)
_MAX_ID = 1000000000

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Logging Configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Logging(object):
    """ Logging Configuration """

    # Color mapping
    COLORS = {
        LOG_ERROR: "red",
        LOG_WARN: "yellow",
        LOG_INFO: "blue",
        LOG_DEBUG: "green",
        LOG_CACHE: "cyan",
        LOG_DATA: "magenta",
    }
    # Environment variable mapping
    MAPPING = {
        0: LOG_WARN,
        1: LOG_INFO,
        2: LOG_DEBUG,
        3: LOG_CACHE,
        4: LOG_DATA,
        5: LOG_ALL,
    }
    # All levels
    LEVELS = "CRITICAL DEBUG ERROR FATAL INFO NOTSET WARN WARNING".split()

    # Default log level is WARN
    _level = LOG_WARN

    class ColoredFormatter(logging.Formatter):
        """ Custom color formatter for logging """
        def format(self, record):
            # Handle custom log level names
            if record.levelno == LOG_ALL:
                levelname = "ALL"
            elif record.levelno == LOG_DATA:
                levelname = "DATA"
            elif record.levelno == LOG_CACHE:
                levelname = "CACHE"
            else:
                levelname = record.levelname
            # Map log level to appropriate color
            try:
                colour = Logging.COLORS[record.levelno]
            except KeyError:
                colour = "black"
            # Color the log level, use brackets when coloring off
            if Coloring().enabled():
                level = color(" " + levelname + " ", "lightwhite", colour)
            else:
                level = "[{0}]".format(levelname)
            return "{0} {1}".format(level, record.getMessage())

    @staticmethod
    def _create_logger():
        """ Create logger """
        # Create logger, handler and formatter
        logger = logging.getLogger('tcms')
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(Logging.ColoredFormatter())
        logger.addHandler(handler)
        # Save log levels in the logger itself (backward compatibility)
        for level in Logging.LEVELS:
            setattr(logger, level, getattr(logging, level))
        # Additional logging constants and methods for cache and xmlrpc
        logger.DATA = LOG_DATA
        logger.CACHE = LOG_CACHE
        logger.ALL = LOG_ALL
        logger.cache = lambda message: logger.log(LOG_CACHE, message)
        logger.data = lambda message: logger.log(LOG_DATA, message)
        logger.all = lambda message: logger.log(LOG_ALL, message)
        return logger

    @staticmethod
    def set(level=None):
        """
        Set the default log level

        If the level is not specified environment variable DEBUG is used
        with the following meaning:

            DEBUG=0 ... LOG_WARN (default)
            DEBUG=1 ... LOG_INFO
            DEBUG=2 ... LOG_DEBUG
            DEBUG=3 ... LOG_CACHE
            DEBUG=4 ... LOG_DATA
            DEBUG=5 ... LOG_ALL (log all messages)
        """

        # If level specified, use given
        if level is not None:
            Logging._level = level
        # Otherwise attempt to detect from the environment
        else:
            try:
                Logging._level = Logging.MAPPING[int(os.environ["DEBUG"])]
            except Exception:
                Logging._level = logging.WARN
        log.setLevel(Logging._level)

    @staticmethod
    def get():
        """ Get the current log level """
        return Logging._level


# Create the logger and detect the log level
log = Logging._create_logger()
set_log_level = Logging.set
get_log_level = Logging.get
set_log_level()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Config Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Config(object):
    """ User configuration """

    # We need only a single config instance
    _instance = None
    _parsed = False
    # Config path
    path = os.path.expanduser("~/.tcms.conf")
    # Minimal config example
    example = ("Please, provide at least a minimal config file {0}:\n"
               "[tcms]\n"
               "url = https://tcms.server/xml-rpc/".format(path))

    def __new__(cls, *args, **kwargs):
        """ Make sure we create a single instance only """
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """ Initialize the configuration """
        # Nothing to do if already parsed
        if self._parsed:
            return

        class Section(object):
            """ Trivial class for sections """
        # Try system settings when the config does not exist in user directory
        if not os.path.exists(self.path):
            log.debug("User config file not found, trying /etc/tcms.conf")
            self.path = "/etc/tcms.conf"
        if not os.path.exists(self.path):
            log.error(self.example)
            raise TCMSError("No config file found")
        log.debug("Parsing config file {0}".format(self.path))

        # Parse the config
        try:
            parser = ConfigParser()
            parser.read([self.path])
            for section in parser.sections():
                # Create a new section object for each section
                setattr(self, section, Section())
                # Set its attributes to section contents (adjust types)
                for name, value in parser.items(section):
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                    if value == "True":
                        value = True
                    if value == "False":
                        value = False
                    setattr(getattr(self, section), name, value)
        except ConfigParser.Error:
            log.error(self.example)
            raise TCMSError(
                "Cannot read the config file")

        # Make sure the server URL is set
        try:
            self.tcms.url is not None
        except AttributeError:
            log.error(self.example)
            raise TCMSError("No url found in the config file")
        self._parsed = True

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Color Configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Coloring(object):
    """ Coloring configuration """

    # Default color mode is auto-detected from the terminal presence
    _mode = None
    MODES = ["COLOR_OFF", "COLOR_ON", "COLOR_AUTO"]
    # We need only a single config instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        """ Make sure we create a single instance only """
        if not cls._instance:
            cls._instance = super(Coloring, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, mode=None):
        """ Initialize the coloring mode """
        # Nothing to do if already initialized
        if self._mode is not None:
            return
        # Set the mode
        self.set(mode)

    def set(self, mode=None):
        """ Set the coloring mode """
        # Detect from the environment if no mode given (only once)
        if mode is None:
            # Nothing to do if already detected
            if self._mode is not None:
                return
            # Detect from the environment variable COLOR
            try:
                mode = int(os.environ["COLOR"])
            except Exception:
                mode = COLOR_AUTO
        elif mode < 0 or mode > 2:
            raise TCMSError("Invalid color mode '{0}'".format(mode))
        self._mode = mode
        log.debug("Coloring {0} ({1})".format(
            "enabled" if self.enabled() else "disabled",
            self.MODES[self._mode]))

    def get(self):
        """ Get the current color mode """
        return self._mode

    def enabled(self):
        """ True if coloring is currently enabled """
        # In auto-detection mode color enabled when terminal attached
        if self._mode == COLOR_AUTO:
            return sys.stdout.isatty()
        return self._mode == COLOR_ON


def set_color_mode(mode):
    """
    Set the coloring mode

    If enabled, some objects (like case run Status) are printed in color
    to easily spot failures, errors and so on. By default the feature is
    enabled when script is attached to a terminal. Possible values are:

        COLOR=0 ... COLOR_OFF .... coloring disabled
        COLOR=1 ... COLOR_ON ..... coloring enabled
        COLOR=2 ... COLOR_AUTO ... if terminal attached (default)

    Environment variable COLOR can be used to set up the coloring to the
    desired mode without modifying code.
    """
    Coloring().set(mode)


def get_color_mode():
    """ Get the current coloring mode """
    return Coloring().get()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Caching Configuration
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Caching(object):
    """ Caching level configuration """

    # Current caching level and the list of all levels
    _level = None
    LEVELS = "CACHE_NONE CACHE_OBJECTS".split()

    # We need only a single config instance
    _instance = None

    def __new__(cls, *args, **kwargs):
        """ Make sure we create a single instance only """
        if not cls._instance:
            cls._instance = super(Caching, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, level=None):
        """ Initialize the caching level """
        # Nothing to do if already initialized
        if self._level is not None:
            return
        # Set the level
        self.set(level)

    def set(self, level=None):
        """ Set the caching level """
        # Setup from the environment or config file (performed only once)
        if level is None:
            # Default cache level already detected, nothing to do
            if self._level is not None:
                return
            # Attempt to detect the level from the environment
            try:
                self._level = int(os.environ.get("CACHE", CACHE_NONE))
            except Exception:
                # Inspect the [cache] section of the config file
                try:
                    self._level = Config().cache.level
                # Use default if no cache section or no config file
                except AttributeError:
                    self._level = CACHE_OBJECTS
        elif level >= CACHE_NONE and level <= CACHE_OBJECTS:
            self._level = level
        else:
            raise TCMSError("Invalid cache level '{0}'".format(level))
        log.debug("Caching on level {0} ({1})".format(
            self._level, self.LEVELS[self._level]))

    def get(self):
        """ Get the current caching level """
        return self._level


def set_cache_level(level):
    """
    Set the caching level

    If the level parameter is not specified environment variable CACHE
    and configuration section [cache] are inspected. There are four cache
    levels available.

        CACHE=0 ... CACHE_NONE
        CACHE=2 ... CACHE_OBJECTS

    See tcms_api.cache module documentation for detailed description
    of the caching mechanism.
    """
    Caching().set(level)


def get_cache_level():
    """ Get the current caching level """
    return Caching().get()
