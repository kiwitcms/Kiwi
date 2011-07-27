"""
High-level API for the Nitrate test case management system.

This module provides a high-level python interface for the nitrate
module. Connection to the server is handled automatically by the
Nitrate object which checks ~/.nitrate config file for the url:

    [nitrate]
    url = https://tcms.engineering.redhat.com/xmlrpc/

"""

import os
import re
import sys
import ConfigParser
import logging as log
from pprint import pformat as pretty

sys.path.append("/usr/share/qa-tools")
from nitrate import NitrateError, NitrateKerbXmlrpc


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Logging
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def setLogLevel(level=None):
    """
    Set the default log level.

    If the level is not specified environment variable DEBUG is used
    with the following meaning:

        DEBUG=0 ... Nitrate.log.WARN (default)
        DEBUG=1 ... Nitrate.log.INFO
        DEBUG=2 ... Nitrate.log.DEBUG
    """

    try:
        if level is None:
            level = {1: log.INFO, 2: log.DEBUG}[int(os.environ["DEBUG"])]
    except StandardError:
        level = log.WARN
    log.basicConfig(format="[%(levelname)s] %(message)s")
    log.getLogger().setLevel(level)

setLogLevel()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Caching
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

CACHE_NONE = 0
CACHE_CHANGES = 1
CACHE_OBJECTS = 2
CACHE_ALL = 3

def setCacheLevel(level=None):
    """
    Set the caching level.

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

    global _cache
    if level is None:
        try:
            _cache = int(os.environ["CACHE"])
        except StandardError:
            _cache = CACHE_OBJECTS
    elif level >= 0 and level <= 3:
        _cache = level
    else:
        raise NitrateError("Invalid cache level '{0}'".format(level))
    log.info("Caching on level {0}".format(_cache))

setCacheLevel()


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Coloring
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

COLOR_ON = 1
COLOR_OFF = 0
COLOR_AUTO = 2

def setColorMode(mode=None):
    """
    Set the coloring mode.

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

    if mode is None:
        try:
            mode = int(os.environ["COLOR"])
        except StandardError:
            mode = COLOR_AUTO
    elif mode < 0 or mode > 2:
        raise NitrateError("Invalid color mode '{0}'".format(mode))

    if mode == COLOR_AUTO:
        _color = sys.stdout.isatty()
    else:
        _color = mode == 1
    log.info("Coloring {0}".format(_color and "enabled" or "disabled"))

def color(text, color=None, background=None, light=False):
    """ Return text in desired color if coloring enabled. """

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

setColorMode()


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
            log.info("Updating {0}'s {1} to '{2}'".format(
                    self.identifier, field, value))
            # Remember modified state if caching
            if _cache:
                self._modified = True
            # Save the changes immediately otherwise
            else:
                self._update()

    return setter


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Nitrate None Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class NitrateNone(object):
    """ Used for distinguish uninitialized values from regular 'None'. """
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
            try:
                path = os.path.expanduser("~/.nitrate")
                parser = ConfigParser.SafeConfigParser()
                parser.read([path])
                Nitrate._settings = dict(parser.items("nitrate"))
            except ConfigParser.Error:
                raise NitrateError(
                        "Cannot read the config file {0}".format(path))

            # We need to know at least the server URL
            if "url" not in self._settings:
                raise NitrateError("No url found in the config file")

        # Return the settings
        return Nitrate._settings

    @property
    def _server(self):
        """ Connection to the server. """

        # Connect to the server unless already connected
        if Nitrate._connection is None:
            log.info("Contacting server {0}".format(self._config["url"]))
            Nitrate._connection = NitrateKerbXmlrpc(
                    self._config["url"]).server

        # Return existing connection
        Nitrate._requests += 1
        return Nitrate._connection

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, prefix="ID"):
        """ Initialize object id and prefix. """
        self._prefix = prefix
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
        """ Short summary about the connection. """
        return "Nitrate server: {0}\nTotal requests handled: {1}".format(
                self._config["url"], self._requests)

    def __eq__(self, other):
        """ Handle object equality based on its id. """
        if not isinstance(other, Nitrate): return False
        return self.id == other.id

    def __ne__(self, other):
        """ Handle object inequality based on its id. """
        return self.id != other.id

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Nitrate Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _get(self):
        """ Fetch object data from the server. """
        raise NitrateError("To be implemented by respective class")


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

    def __str__(self):
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
                log.debug("Intializing build " + self.identifier)
                log.debug(pretty(hash))
                self._name = hash["name"]
                self._product = Product(hash["product_id"])
            except LookupError:
                raise NitrateError(
                        "Cannot find build for " + self.identifier)
        # Search by product and name
        else:
            try:
                log.info("Fetching build '{0}' of '{1}'".format(
                        self.name, self.product.name))
                hash = self._server.Build.check_build(
                        self.name, self.product.id)
                log.debug("Initializing build '{0}' of '{1}'".format(
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

    def __init__(self, id=None, product=None, category=None):
        """ Initialize by category id or product and category name. """

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

    def __str__(self):
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
                log.debug("Intializing category " + self.identifier)
                log.debug(pretty(hash))
                self._name = hash["name"]
                self._product = Product(hash["product_id"])
            except LookupError:
                raise NitrateError(
                        "Cannot find category for " + self.identifier)
        # Search by product and name
        else:
            try:
                log.info("Fetching category '{0}' of '{1}'".format(
                        self.name, self.product.name))
                hash = self._server.Product.check_category(
                        self.name, self.product.id)
                log.debug("Initializing category '{0}' of '{1}'".format(
                        self.name, self.product.name))
                log.debug(pretty(hash))
                self._id = hash["id"]
            except LookupError:
                raise NitrateError("Category '{0}' not found in '{1}'".format(
                    self.name, self.product.name))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Plan Type Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanType(Nitrate):
    """ Plan type. """

    _plantypes = ['Null', 'Unit', 'Integration', 'Function', 'System',
                    'Acceptance', 'Installation', 'Performance', 'Product',
                    'Interoperability', 'Smoke', 'Regression', 'NotExist',
                    'i18n/l10n', 'Load', 'Sanity', 'Functionality', 'Stress',
                    'Stability', 'Density', 'Benchmark', 'testtest', 'test11',
                    'Place Holder', 'Recovery', 'Component', 'General', 'Release']

    def __init__(self, plantype):
        """
        Takes numeric Test Plan Type id or name
        """

        if isinstance(plantype, int):
            if plantype < 1 or plantype > 28 or plantype == 12:
                raise NitrateError(
                    "Not a valid Test Plan Type id: '{0}'".format(plantype))
            self._id = plantype
        else:
            try:
                self._id = self._plantypes.index(plantype)
            except ValueError:
                raise NitrateError(
                    "Invalid Test Plan type '{0}'".format(plantype))

    def __str__(self):
        """ Return TestPlan type for printing. """
        return self.name

    @property
    def id(self):
        """ Numeric TestPlan type id. """
        return self._id

    @property
    def name(self):
        """ Human readable TestPlan type name. """
        return self._plantypes[self._id]



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

    def __str__(self):
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

    def __str__(self):
        """ Product name for printing. """
        if self._version is not NitrateNone:
            return "{0}, version {1}".format(self.name, self.version)
        else:
            return self.name

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
                log.info("Fetching product '{0}'".format(self.name))
                hash = self._server.Product.filter({'name': self.name})[0]
                log.debug("Initializing product '{0}'".format(self.name))
                log.debug(pretty(hash))
                self._id = hash["id"]
            except IndexError:
                raise NitrateError(
                        "Cannot find product for '{0}'".format(self.name))


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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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
        if hash is None and _cache == CACHE_ALL and not User._users:
            log.info("Caching all users")
            for hash in Nitrate()._server.User.filter({}):
                user = User(hash=hash)
                User._users[user.id] = user
        if hash is None and _cache >= CACHE_OBJECTS and id is not None:
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

    def __str__(self):
        """ User login for printing. """
        return self.login

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

    def __str__(self):
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
                log.info("Fetching version '{0}' of '{1}'".format(
                        self.name, self.product.name))
                hash = self._server.Product.filter_versions(
                        {'product': self.product.id, 'value': self.name})
                log.debug("Initializing version '{0}' of '{1}'".format(
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
            log.exception("Failed to update {0}".format(self))

    def _update(self):
        """ Save data to server (to be implemented by respective class) """
        raise NitrateError("Data update not implemented")

    def update(self):
        """ Update the data, if modified, to the server """
        if self._modified:
            self._update()
            self._modified = False


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

    def __str__(self):
        """ Bug name for printing. """
        return "BZ#{0}".format(self.bug)

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

    def __str__(self):
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
            log.info("Attaching bug {0} to {1}".format(
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
            log.info("{0} not attached to {1}, doing nothing".format(
                    bug, self._object.identifier))
        # Detach the bug
        else:
            # Fetch the complete bug object (including the internal id)
            bug = [bugg for bugg in self if bugg == bug][0]
            log.info("Detaching {0}".format(self.synopsis))
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
#  Tags Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Tags(Mutable):
    """ Tag list for test plan, test run or test case objects. """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Tags Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    id = property(_getter("id"), doc="Tagged object id.")

    @property
    def _tags(self):
        """ Set representation of the tags. """
        if self._current is NitrateNone:
            self._get()
        return self._current

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Tags Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, object):
        """ Initialize tags for specified object. """
        Mutable.__init__(self, object.id)
        self._class = object.__class__
        self._identifier = object.identifier
        self._current = NitrateNone
        self._original = NitrateNone

    def __iter__(self):
        """ Tag iterator. """
        for tag in self._tags:
            yield tag

    def __contains__(self, tag):
        """ Tag 'in' operator. """
        return tag in self._tags

    def __str__(self):
        """ Display tags as list for printing. """
        return "{0}'s tags: {1}".format(self._identifier,
                ", ".join(sorted(self._tags)) or "[NoTags]")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Tags Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def add(self, tag):
        """ Add a tag, mark as modified. """
        if tag not in self._tags:
            self._tags.add(tag)
            if _cache:
                self._modified = True
            else:
                self._update()

    def remove(self, tag):
        """ Remove a tag, mark as modified. """
        if tag in self._tags:
            self._tags.remove(tag)
            if _cache:
                self._modified = True
            else:
                self._update()

    def _get(self):
        """ Initialize / refresh object tags from the server. """
        log.info("Fetching tags for {0}".format(self._identifier))
        # Use the respective XMLRPC call to get the tags
        if self._class is TestPlan:
            hash = self._server.TestPlan.get_tags(self.id)
        elif self._class is TestRun:
            hash = self._server.TestRun.get_tags(self.id)
        elif self._class is TestCase:
            hash = self._server.TestCase.get_tags(self.id)
        else:
            raise NitrateError("Not tag support for {0}".format(self._class))
        log.debug(pretty(hash))

        # Save the tag list as set, note the initial state
        self._current = set([tag["name"] for tag in hash])
        self._original = set(self._tags)

    def _update(self):
        """ Save tag changes to the server. """
        # Added tags
        added = self._current - self._original
        if added:
            log.info("Tagging {0} with '{1}'".format(
                    self._identifier, ", ".join(added)))
            if self._class is TestPlan:
                self._server.TestPlan.add_tag(self.id, list(added))
            elif self._class is TestRun:
                self._server.TestRun.add_tag(self.id, list(added))
            elif self._class is TestCase:
                self._server.TestCase.add_tag(self.id, list(added))

        # Removed tags
        removed = self._original - self._current
        if removed:
            log.info("Untagging {0} of '{1}'".format(
                    self._identifier, ", ".join(removed)))
            if self._class is TestPlan:
                self._server.TestPlan.remove_tag(self.id, list(removed))
            elif self._class is TestRun:
                self._server.TestRun.remove_tag(self.id, list(removed))
            elif self._class is TestCase:
                self._server.TestCase.remove_tag(self.id, list(removed))

        # Save the current state as the original (for future updates)
        self._original = set(self._current)


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

    # Read-write properties
    name = property(_getter("name"), _setter("name"),
            doc="Test plan name.")
    parent = property(_getter("parent"), _setter("parent"),
            doc="Parent test plan.")
    product = property(_getter("product"), _setter("product"),
            doc="Test plan product.")
    type = property(_getter("type"), _setter("type"),
            doc="Test plan type.")

    @property
    def testruns(self):
        """ List of TestRun() objects related to this plan. """
        if self._testruns is NitrateNone:
            self._testruns = [TestRun(testrunhash=hash) for hash in
                    self._server.TestPlan.get_test_runs(self.id)]
        return self._testruns

    @property
    def testcases(self):
        """ List of TestCase() objects related to this plan. """
        if self._testcases is NitrateNone:
            self._testcases = [TestCase(testcasehash=hash) for hash in
                    self._server.TestPlan.get_test_cases(self.id)]
        return self._testcases

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

        """ Initialize a test plan or create a new one.

        Provide id to initialize an existing plan, name, product, version
        and type to create a new plan.
        Other parameters are optional and have following defaults:

            document .... ""
            parent ...... None
            is_active ... 1

        """

        Mutable.__init__(self, id, prefix="TP")

        # Initialize values to unknown
        for attr in """id author name parent product type testcases
                testruns tags""".split():
            setattr(self, "_" + attr, NitrateNone)

        # Optionally we can get prepared hash
        testplanhash = kwargs.get("testplanhash", None)

        # If id provided, initialization happens only when data requested
        if id:
            self._id = id
        # If hash provided, let's initialize the data immediately
        elif testplanhash:
            self._id = testplanhash["plan_id"]
            self._get(testplanhash=testplanhash)
        # Create a new test plan based on provided name, type and product
        elif name and type and product:
            self._create(name=name, product=product, version=version, type=type, **kwargs)
        else:
            raise NitrateError("Need either id or name, product, version and type")

    def __iter__(self):
        """ Provide test cases as the default iterator. """
        for testcase in self.testcases:
            yield testcase

    def __str__(self):
        """ Test plan id & summary for printing. """
        return "{0} - {1}".format(self.identifier, self.name)

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
            type = PlanType(type)
        hash["type"] = type.id

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
        log.info("Successfully created {0}".format(self))

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

        # Set up attributes
        self._author = User(testplanhash["author_id"])
        self._name = testplanhash["name"]
        self._product = Product(id=testplanhash["product_id"],
                version=testplanhash["default_product_version"])
        self._type = PlanType(testplanhash["type_id"])
        if testplanhash["parent_id"] is not None:
            self._parent = TestPlan(testplanhash["parent_id"])
        else:
            self._parent = None
        self._tags = Tags(self)

    def _update(self):
        """ Save test plan data to the server. """

        # Prepare the update hash
        hash = {}
        hash["name"] = self.name
        hash["product"] = self.product.id
        hash["type"] = self.type.id
        if self.parent is not None:
            hash["parent"] = self.parent.id
        # Disabled until BZ#716499 is fixed
        # TODO hash["default_product_version"] = self.product.version.id

        log.info("Updating test plan " + self.identifier)
        log.debug(pretty(hash))
        self._server.TestPlan.update(self.id, hash)


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
    product = property(_getter("product"), _setter("product"),
            doc="Product relevant for this test run.")
    status = property(_getter("status"), _setter("status"),
            doc="Test run status")
    summary = property(_getter("summary"), _setter("summary"),
            doc="Test run summary.")
    tester = property(_getter("tester"), _setter("tester"),
            doc="Default tester.")
    time = property(_getter("time"), _setter("time"),
            doc="Estimated time.")

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

            build ..... "unspecified"
            product ... test plan product
            version ... test plan product version
            summary ... <test plan name> on <build>
            notes ..... ""
            manager ... current user
            tester .... current user
            tags ...... None

        Tags should be provided as a list of tag names.
        """

        Mutable.__init__(self, id, prefix="TR")

        # Initialize values to unknown
        for attr in """id testplan build manager summary product tester time
                notes status tags caseruns""".split():
            setattr(self, "_" + attr, NitrateNone)

        # Optionally we can get prepared hash
        testrunhash = kwargs.get("testrunhash", None)

        # If id provided, initialization happens only when data requested
        if id:
            self._id = id
        # If hash provided, let's initialize the data immediately
        elif testrunhash:
            self._id = testrunhash["run_id"]
            self._get(testrunhash=testrunhash)
        # Create a new test run based on provided plan
        elif testplan:
            self._create(testplan=testplan, **kwargs)
        else:
            raise NitrateError(
                    "Need either id or test plan to initialize test run")

    def __iter__(self):
        """ Provide test case runs as the default iterator. """
        for caserun in self.caseruns:
            yield caserun

    def __str__(self):
        """ Test run id & summary for printing. """
        return "{0} - {1}".format(self.identifier, self.summary)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Run Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, testplan, product=None, version=None, build=None,
            summary=None, notes=None, manager=None, tester=None, tags=None,
            **kwargs):
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

        # Build
        if build is None:
            build = "unspecified"
        if isinstance(build, basestring):
            build = Build(build=build, product=product)
        hash["build"] = build.id

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

        # Include all test cases and tag with supplied tags
        hash["case"] = [case.id for case in testplan]
        if tags: hash["tag"] = ",".join(tags)

        # Submit to the server and initialize
        log.info("Creating a new test run based on {0}".format(testplan))
        log.debug(pretty(hash))
        testrunhash = self._server.TestRun.create(hash)
        log.debug(pretty(testrunhash))
        try:
            self._id = testrunhash["run_id"]
        except TypeError:
            log.error("Failed to create a new test run based on {0}".format(
                    testplan))
            log.error(pretty(hash))
            log.error(pretty(testrunhash))
            raise NitrateError("Failed to create test run")
        self._get(testrunhash=testrunhash)

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
        # Work around BZ#716233 (uses build product)
        self._product = Product(id=self.build.product.id,
                version=testrunhash["product_version"])
        self._tags = Tags(self)

    def _update(self):
        """ Save test run data to the server. """

        # Prepare the update hash
        hash = {}
        hash["build"] = self.build.id
        hash["default_tester"] = self.tester.id
        hash["estimated_time"] = self.time
        hash["manager"] = self.manager.id
        hash["notes"] = self.notes
        hash["product"] = self.product.id
        hash["product_version"] = self.product.version.id
        hash["status"] = self.status.id
        hash["summary"] = self.summary

        log.info("Updating test run " + self.identifier)
        log.debug(pretty(hash))
        self._server.TestRun.update(self.id, hash)


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

    @property
    def synopsis(self):
        """ Short summary about the test case. """
        plans = len(self.testplans)
        return "{0} ({1}, {2}, {3}, {4} {5})".format(
                self, self.category, self.priority, self.status,
                plans, "test plan" if plans == 1 else "test plans")

    # Read-write properties
    automated = property(_getter("automated"), _setter("automated"),
            doc="Automation flag.")
    arguments = property(_getter("arguments"), _setter("arguments"),
            doc="Test script arguments (used for automation).")
    category = property(_getter("category"), _setter("category"),
            doc="Test case category.")
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

    @property
    def components(self):
        """ Related components. """
        if self._components is NitrateNone:
            self._components = [Component(componenthash=hash) for hash in
                    self._server.TestCase.get_components(self.id)]
        return self._components

    @property
    def testplans(self):
        """ List of TestPlan() objects linked to this test case. """
        if self._testplans is NitrateNone:
            self._testplans = [TestPlan(testplanhash=hash)
                    for hash in self._server.TestCase.get_plans(self.id)]
        return self._testplans

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, summary=None, category=None, product=None,
            priority=None, **kwargs):
        """ Initialize a test case or create a new one.

        Initialize an existing test case (if id provided) or create a
        new one (based on provided summary, category, product and
        priority).
        """

        Mutable.__init__(self, id, prefix="TC")

        # Initialize values to unknown
        for attr in """product category priority summary status plans
                components tester time automated sortkey script arguments
                tags testplans bugs author""".split():
            setattr(self, "_" + attr, NitrateNone)

        # Optionally we can get prepared hash
        testcasehash = kwargs.get("testcasehash", None)

        # If id provided, initialization happens only when data requested
        if id:
            self._id = id
        # If hash provided, let's initialize the data immediately
        elif testcasehash:
            self._id = testcasehash["case_id"]
            self._get(testcasehash=testcasehash)
        # Create a new test case based on case, run and build
        elif summary and category and product and priority:
            self._create(summary=summary, category=category, product=product,
                    priority=priority)
        else:
            raise NitrateError("Need either id or "
                    "summary, category, product and priority")

    def __str__(self):
        """ Test case id & summary for printing. """
        return "{0} - {1}".format(self.identifier.ljust(8), self.summary)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Test Case Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, summary, category, product, priority, **kwargs):
        """ Create a new test case. """
        raise NitrateError("To be implemented")


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
        self._automated = testcasehash["is_automated"]
        self._category = Category(testcasehash["category_id"])
        self._notes = testcasehash["notes"]
        self._priority = Priority(testcasehash["priority_id"])
        self._requirement = testcasehash["requirement"]
        self._script = testcasehash["script"]
        # XXX self._sortkey = testcasehash["sortkey"]
        self._status = CaseStatus(testcasehash["case_status_id"])
        self._summary = testcasehash["summary"]
        self._tags = Tags(self)
        self._time = testcasehash["estimated_time"]
        if testcasehash["default_tester_id"] is not None:
            self._tester = User(testcasehash["default_tester_id"])
        else:
            self._tester = None
        self._bugs = Bugs(self)

    def _update(self):
        """ Save test case data to server """
        hash = {}

        hash["arguments"] = self.arguments
        hash["case_status"] = self.status.id
        hash["category"] = self.category.id
        hash["estimated_time"] = self.time
        hash["is_automated"] = self.automated
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

    def __init__(self, id=None, testcase=None, testrun=None, build=None,
            **kwargs):
        """ Initialize a test case run or create a new one.

        Initialize an existing test case run (if id provided) or create
        a new test case run (based on provided test case, test run and
        build).
        """

        Mutable.__init__(self, id, prefix="CR")

        # Initialize values to unknown
        for attr in """assignee bugs build notes sortkey status testcase
                testrun""".split():
            setattr(self, "_" + attr, NitrateNone)

        # Optionally we can get prepared hashes
        caserunhash = kwargs.get("caserunhash", None)
        testcasehash = kwargs.get("testcasehash", None)

        # If id provided, initialization happens only when data requested
        if id:
            self._id = id
        # If hashes provided, let's initialize the data immediately
        elif caserunhash and testcasehash:
            self._id = caserunhash["case_run_id"]
            self._get(caserunhash=caserunhash, testcasehash=testcasehash)
        # Create a new test case run based on case, run and build
        elif testcase and testrun and build:
            self._create(testcase=testcase, testrun=testrun, build=build)
        else:
            raise NitrateError("Need either id or testcase, testrun & build")

    def __str__(self):
        """ Case run id, status & summary for printing. """
        return "{0} - {1} - {2}".format(self.status.shortname,
                self.identifier.ljust(9), self.testcase.summary)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Case Run Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(testcase, testrun, build, **kwargs):
        """ Create a new case run. """
        raise NitrateError("To be implemented")

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
        self._sortkey = caserunhash["sortkey"]
        self._status = Status(caserunhash["case_run_status_id"])
        self._testrun = TestRun(caserunhash["run_id"])
        if testcasehash:
            self._testcase = TestCase(testcasehash=testcasehash)
        else:
            self._testcase = TestCase(caserunhash["case_id"])
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


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Self Test
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    # Display info about the server
    print Nitrate()

    # Show test plan summary and list test cases
    testplan = TestPlan(289)
    print "\n", testplan.synopsis
    for testcase in testplan:
        print " ", testcase

    # For each test run list test cases with their status
    for testrun in testplan.testruns:
        print "\n", testrun.synopsis
        for caserun in testrun:
            print " ", caserun

    # Update test case data / case run status
    TestPlan(289).name = "Tessst plan"
    TestRun(6757).notes = "Testing notes"
    TestCase(46490).script = "/CoreOS/component/example"
    CaseRun(525318).status = Status("PASSED")
    TestRun(6757).tags.add("TestTag")
    TestRun(6757).status = RunStatus("FINISHED")

    # Display info about the server
    print "\n", Nitrate()
