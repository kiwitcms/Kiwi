# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
#   Copyright (c) 2018 Kiwi TCMS project. All rights reserved.
#   Author: Alexander Todorov <info@kiwitcms.org>
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
Immutable TCMS objects
"""

from pprint import pformat as pretty

import tcms_api.config as config

from tcms_api.config import log
from tcms_api.base import TCMS, TCMSNone, _getter, _idify
from tcms_api.xmlrpc import TCMSError

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Build Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Build(TCMS):
    """ Product build """

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
        """ Initialize by build id or product and build name """

        # Backward compatibility for 'build' argument (now called 'name')
        name = name if name is not None else kwargs.get("build")

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id or name)
        if initialized:
            return
        TCMS.__init__(self, id)

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
            if self.product._name is not TCMSNone:
                self._index("{0}---in---{1}".format(
                    self.name, self.product.name))
        # Otherwise just check that the id was provided
        elif not id:
            raise TCMSError("Need either build id or both build name "
                            "and product to initialize the Build object.")

    def __str__(self):
        """ Build name for printing """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Build Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing build data """
        TCMS._fetch(self, inject)
        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing build ID#{0} inject".format(
                inject["build_id"]))
        # Search by build id
        elif self._id is not TCMSNone:
            try:
                log.info("Fetching build " + self.identifier)
                inject = self._server.Build.filter({'pk': self.id})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError(
                    "Cannot find build for " + self.identifier)
        # Search by build name and product
        else:
            try:
                log.info("Fetching build '{0}' of '{1}'".format(
                    self.name, self.product.name))
                inject = self._server.Build.filter({
                    'name': self.name,
                    'product': self.product.id
                })[0]
                self._id = inject["build_id"]
            except IndexError as error:
                log.debug(error)
                raise TCMSError("Build '{0}' not found in '{1}'".format(
                    self.name, self.product.name))
            except KeyError:
                if "args" in inject:
                    log.debug(inject["args"])
                raise TCMSError("Build '{0}' not found in '{1}'".format(
                    self.name, self.product.name))

        # Initialize data from the inject and index into cache
        log.debug("Initializing Build ID#{0}".format(inject["build_id"]))
        log.data(pretty(inject))
        self._inject = inject
        self._id = inject["build_id"]
        self._name = inject["name"]
        self._product = Product(
            {"id": inject["product_id"], "name": inject["product"]})
        self._index("{0}---in---{1}".format(self.name, self.product.name))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Category Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Category(TCMS):
    """ Test case category """

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
        """ Short category summary (including product info) """
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
        if initialized:
            return
        TCMS.__init__(self, id)

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
            if self.product._name is not TCMSNone:
                self._index("{0}---in---{1}".format(
                    self.name, self.product.name))
        # Otherwise just check that the id was provided
        elif not id:
            raise TCMSError("Need either category id or both category "
                            "name and product to initialize the Category object.")

    def __str__(self):
        """ Category name for printing """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Category Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing category data """
        TCMS._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing category ID#{0} inject".format(inject["id"]))
        # Search by category id
        elif self._id is not TCMSNone:
            try:
                log.info("Fetching category {0}".format(self.identifier))
                inject = self._server.Category.filter({'pk': self.id})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError(
                    "Cannot find category for " + self.identifier)
        # Search by category name and product
        else:
            try:
                log.info("Fetching category '{0}' of '{1}'".format(
                    self.name, self.product.name))
                inject = self._server.Category.filter({
                    'name': self.name,
                    'product': self.product.id
                })[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError("Category '{0}' not found in"
                                " '{1}'".format(self.name, self.product.name))

        # Initialize data from the inject and index into cache
        log.debug("Initializing category ID#{0}".format(inject["id"]))
        log.data(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["name"]
        self._product = Product(
            {"id": inject["product_id"], "name": inject["product"]})
        self._index("{0}---in---{1}".format(self.name, self.product.name))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanType Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanType(TCMS):
    """ Plan type """

    # Local cache of PlanType objects indexed by plan type id
    _cache = {}

    # By default we cache PlanType objects for ever
    _expiration = config.NEVER_EXPIRE

    # List of all object attributes (used for init & expiration)
    _attributes = ["name"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanType Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Test plan type id")
    name = property(_getter("name"), doc="Test plan type name")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanType Decorated
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
    #  PlanType Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, name=None):
        """ Initialize by test plan type id or name """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id or name)
        if initialized:
            return
        TCMS.__init__(self, id)

        # If inject given, fetch data from it
        if inject:
            self._fetch(inject)
        # Initialize by name
        elif name is not None:
            self._name = name
            self._index(name)
        # Otherwise just check that the test plan type id was provided
        elif not id:
            raise TCMSError(
                "Need either id or name to initialize the PlanType object")

    def __str__(self):
        """ PlanType name for printing """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  PlanType Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing test plan type data """
        TCMS._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing PlanType ID#{0} inject".format(inject["id"]))
        # Search by test plan type id
        elif self._id is not TCMSNone:
            try:
                log.info("Fetching test plan type " + self.identifier)
                inject = self._server.PlanType.filter({'pk': self.id})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError(
                    "Cannot find test plan type for " + self.identifier)
        # Search by test plan type name
        else:
            try:
                log.info("Fetching test plan type '{0}'".format(self.name))
                inject = self._server.PlanType.filter({'name': self.name})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError("PlanType '{0}' not found".format(
                    self.name))
        # Initialize data from the inject and index into cache
        log.debug("Initializing PlanType ID#{0}".format(inject["id"]))
        log.data(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["name"]
        self._index(self.name)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Priority Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Priority(TCMS):
    """ Test case priority """

    _priorities = ['P0', 'P1', 'P2', 'P3', 'P4', 'P5']

    def __init__(self, priority):
        """
        Takes numeric priority id (1-5) or priority name which is one of:
        P1, P2, P3, P4, P5
        """

        if isinstance(priority, int):
            if priority < 1 or priority > 5:
                raise TCMSError(
                    "Not a valid Priority id: '{0}'".format(priority))
            self._id = priority
        else:
            try:
                self._id = self._priorities.index(priority)
            except ValueError:
                raise TCMSError("Invalid priority '{0}'".format(priority))

    def __str__(self):
        """ Return priority name for printing """
        return self.name

    @property
    def id(self):
        """ Numeric priority id """
        return self._id

    @property
    def name(self):
        """ Human readable priority name """
        return self._priorities[self._id]

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Product Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Product(TCMS):
    """ Product """

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
        if initialized:
            return
        TCMS.__init__(self, id)

        # If inject given, fetch test case data from it
        if inject:
            self._fetch(inject)
        # Initialize by name
        elif name is not None:
            self._name = name
            self._index(name)
        # Otherwise just check that the product id was provided
        elif not id:
            raise TCMSError("Need id or name to initialize Product")

    def __str__(self):
        """ Product name for printing """
        return self.name

    @staticmethod
    def search(**query):
        """ Search for products """
        return [Product(hash["id"])
                for hash in TCMS()._server.Product.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Product Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch product data from the server """
        TCMS._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.debug("Initializing Product ID#{0}".format(inject["id"]))
            log.data(pretty(inject))
            self._id = inject["id"]
            self._name = inject["name"]
        # Search by product id
        elif self._id is not TCMSNone:
            try:
                log.info("Fetching product " + self.identifier)
                inject = self._server.Product.filter({'id': self.id})[0]
                log.debug("Initializing product " + self.identifier)
                log.data(pretty(inject))
                self._inject = inject
                self._name = inject["name"]
            except IndexError:
                raise TCMSError(
                    "Cannot find product for " + self.identifier)
        # Search by product name
        else:
            try:
                log.info("Fetching product '{0}'".format(self.name))
                inject = self._server.Product.filter({'name': self.name})[0]
                log.debug("Initializing product '{0}'".format(self.name))
                log.data(pretty(inject))
                self._inject = inject
                self._id = inject["id"]
            except IndexError:
                raise TCMSError(
                    "Cannot find product for '{0}'".format(self.name))
        # Index the fetched object into cache
        self._index(self.name)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseStatus Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseStatus(TCMS):
    """ Test case status """

    _casestatuses = ['PAD', 'PROPOSED', 'CONFIRMED', 'DISABLED', 'NEED_UPDATE']

    def __init__(self, casestatus):
        """
        Takes numeric status id (1-4) or status name which is one of:
        PROPOSED, CONFIRMED, DISABLED, NEED_UPDATE
        """
        if isinstance(casestatus, int):
            if casestatus < 1 or casestatus > 4:
                raise TCMSError(
                    "Not a valid casestatus id: '{0}'".format(casestatus))
            self._id = casestatus
        else:
            try:
                self._id = self._casestatuses.index(casestatus)
            except ValueError:
                raise TCMSError(
                    "Invalid casestatus '{0}'".format(casestatus))

    def __str__(self):
        """ Return casestatus name for printing """
        return self.name

    @property
    def id(self):
        """ Numeric casestatus id """
        return self._id

    @property
    def name(self):
        """ Human readable casestatus name """
        return self._casestatuses[self._id]


class TestCaseRunStatus(TCMS):
    """
    Test case run status.

    Used for easy converting between id and name.
    """

    # FIXME: this relies on statuses in Db having the same order because
    # we pass around IDs in other parts of the code. This can go wrong in
    # so many ways
    _statuses = ['PAD', 'IDLE', 'RUNNING', 'PAUSED', 'PASSED', 'FAILED',
                 'BLOCKED', 'ERROR', 'WAIVED']

    def __init__(self, status):
        """
        Takes numeric status id (1-8) or status name which is one of:
        IDLE, PASSED, FAILED, RUNNING, PAUSED, BLOCKED, ERROR, WAIVED
        """
        if isinstance(status, int):
            if status < 1 or status > 8:
                raise TCMSError(
                    "Not a valid Status id: '{0}'".format(status))
            self._id = status
        else:
            try:
                self._id = self._statuses.index(status)
            except ValueError:
                raise TCMSError("Invalid status '{0}'".format(status))

    def __str__(self):
        """ Return status name for printing """
        return self.name

    @property
    def id(self):
        """ Numeric status id """
        return self._id

    @property
    def name(self):
        """ Human readable status name """
        return self._statuses[self.id]

    @property
    def shortname(self):
        """ Short same-width status string (4 chars) """
        return self.name[0:4]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  User Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class User(TCMS):
    """ User """

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
        """ Search for users """
        return [User(hash)
                for hash in TCMS()._server.User.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __new__(cls, id=None, *args, **kwargs):
        """ Create a new object, handle caching if enabled """
        # Convert login or email into name for better logging
        if "login" in kwargs or "email" in kwargs:
            name = kwargs.get("login", kwargs.get("email"))
            return TCMS.__new__(cls, id=id, name=name, *args, **kwargs)
        else:
            return TCMS.__new__(cls, id=id, *args, **kwargs)

    def __init__(self, id=None, login=None, email=None):
        """
        Initialize by user id, login or email

        Defaults to the current user if no id, login or email provided.
        If xmlrpc initial object dict provided as the first argument,
        data are initialized directly from it.
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id or login or email)
        if initialized:
            return
        TCMS.__init__(self, id, prefix="UID")

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

    def __str__(self):
        """ User login for printing """
        return self.name if self.name is not None else "No Name"

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  User Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch user data from the server """
        TCMS._fetch(self, inject)

        if inject is None:
            # Search by id
            if self._id is not TCMSNone:
                try:
                    log.info("Fetching user " + self.identifier)
                    inject = self._server.User.filter({"id": self.id})[0]
                except IndexError:
                    raise TCMSError(
                        "Cannot find user for " + self.identifier)
            # Search by login
            elif self._login is not TCMSNone:
                try:
                    log.info("Fetching user for login '{0}'".format(self.login))
                    inject = self._server.User.filter({"username": self.login})[0]
                except IndexError:
                    raise TCMSError("No user found for login '{0}'".format(self.login))
            # Search by email
            elif self._email is not TCMSNone:
                try:
                    log.info("Fetching user for email '{0}'".format(self.email))
                    inject = self._server.User.filter({"email": self.email})[0]
                except IndexError:
                    raise TCMSError("No user found for email '{0}'".format(self.email))
            # Otherwise initialize to the current user
            else:
                log.info("Fetching the current user")
                inject = self._server.User.filter()[0]
                self._index("i-am-current-user")

        # Initialize data from the inject and index into cache
        log.debug("Initializing user UID#{0}".format(inject["id"]))
        log.data(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._login = inject["username"]
        self._email = inject["email"]
        if inject["first_name"] and inject["last_name"]:
            self._name = inject["first_name"] + " " + inject["last_name"]
        else:
            self._name = None
        self._index(self.login, self.email)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Version Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Version(TCMS):
    """ Product version """

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
        """ Initialize by version id or product and version """

        # Backward compatibility for 'version' argument (now called 'name')
        name = name if name is not None else kwargs.get("version")

        # Initialize (unless already done)
        id, ignore, inject, initialized = self._is_initialized(id)
        if initialized:
            return
        TCMS.__init__(self, id)

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
            if self.product._name is not TCMSNone:
                self._index("{0}---in---{1}".format(self.name, self.product.name))
        # Otherwise just make sure the version id was provided
        elif not id:
            raise TCMSError("Need either version id or both product "
                            "and version name to initialize the Version object.")

    def __str__(self):
        """ Version name for printing """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Version Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch version data from the server """
        TCMS._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.debug("Processing Version ID#{0} inject".format(inject["id"]))
        # Search by version id
        elif self._id is not TCMSNone:
            try:
                log.info("Fetching version {0}".format(self.identifier))
                inject = self._server.Version.filter({'id': self.id})[0]
            except IndexError:
                raise TCMSError(
                    "Cannot find version for {0}".format(self.identifier))
        # Search by product and name
        else:
            try:
                log.info("Fetching version '{0}' of '{1}'".format(
                    self.name, self.product.name))
                inject = self._server.Version.filter(
                    {'product': self.product.id, 'value': self.name})[0]
            except IndexError:
                raise TCMSError(
                    "Cannot find version for '{0}'".format(self.name))
        # Initialize data from the inject and index into cache
        log.debug("Initializing Version ID#{0}".format(inject["id"]))
        log.data(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["value"]
        self._product = Product(inject["product_id"])
        # Index by product name & version name (if product is cached)
        if self.product._name is not TCMSNone:
            self._index("{0}---in---{1}".format(self.name, self.product.name))
        # Otherwise index by id only
        else:
            self._index()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Component Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Component(TCMS):
    """ Test case component """

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
        """ Short component summary (including product info) """
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
        if initialized:
            return
        TCMS.__init__(self, id)

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
            if self.product._name is not TCMSNone:
                self._index("{0}---in---{1}".format(
                    self.name, self.product.name))
        # Otherwise just check that the id was provided
        elif id is None:
            raise TCMSError("Need either component id or both product "
                            "and component name to initialize the Component object.")

    def __str__(self):
        """ Component name for printing """
        return self.name

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Component Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Get the missing component data """
        TCMS._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.info("Processing component ID#{0} inject".format(inject["id"]))
        # Search by component id
        elif self._id is not TCMSNone:
            try:
                log.info("Fetching component " + self.identifier)
                inject = self._server.Component.filter({'pk': self.id})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError(
                    "Cannot find component for " + self.identifier)
        # Search by component name and product
        else:
            try:
                log.info("Fetching component '{0}' of '{1}'".format(
                    self.name, self.product.name))
                inject = self._server.Component.filter({
                    'name': self.name,
                    'product': self.product.id
                })[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError("Component '{0}' not found in"
                                " '{1}'".format(self.name, self.product.name))

        # Initialize data from the inject and index into cache
        log.debug("Initializing component ID#{0}".format(inject["id"]))
        log.data(pretty(inject))
        self._inject = inject
        self._id = inject["id"]
        self._name = inject["name"]
        self._product = Product(
            {"id": inject["product_id"], "name": inject["product"]})
        self._index("{0}---in---{1}".format(self.name, self.product.name))

    @staticmethod
    def search(**query):
        """ Search for components """
        return [Component(hash) for hash in
                TCMS()._server.Component.filter(dict(query))]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Bug Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Bug(TCMS):
    """ Bug related to a test case or a case run """

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
        if initialized:
            return
        TCMS.__init__(self, id, prefix="BUG")

        # If inject given, fetch bug data from it
        if inject:
            self._fetch(inject)
        # Initialized by bug id and system id
        elif bug is not None and system is not None:
            self._bug = bug
            self._system = system
        # Otherwise just check that the id was provided
        elif id is None:
            raise TCMSError("Need bug id to initialize the Bug object.")

    def __eq__(self, other):
        """
        Custom bug comparison

        Primarily decided by id. If unknown, compares by bug id & bug system.
        """
        # Decide by internal id
        if self._id is not TCMSNone and other._id is not TCMSNone:
            return self.id == other.id
        # Compare external id and bug system id
        return self.bug == other.bug and self.system == other.system

    def __str__(self):
        """ Bug name for printing """
        try:
            prefix = self._prefixes[self.system]
        except KeyError:
            prefix = "BZ"
        return "{0}#{1}".format(prefix, str(self.bug).rjust(
            self._identifier_width, "0"))

    def __hash__(self):
        """ Construct the uniqe hash from bug id and bug system id """
        return _idify([self.system, self.bug])

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Bug Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch bug info from the server """
        TCMS._fetch(self, inject)
        # No direct xmlrpc function for fetching so far
        if inject is None:
            raise NotImplementedError("Direct bug fetching not implemented")
        # Process provided inject
        self._id = int(inject["id"])
        self._bug = int(inject["bug_id"])
        self._system = int(inject["bug_system_id"])
        self._testcase = TestCase(int(inject["case_id"]))
        if inject["case_run_id"] is not None:
            self._caserun = TestCaseRun(int(inject["case_run_id"]))
        # Index the fetched object into cache
        self._index()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Tag Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Tag(TCMS):
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
        if initialized:
            return
        TCMS.__init__(self, id)

        # If inject given, fetch tag data from it
        if inject:
            self._fetch(inject)
        # Initialize by name
        elif name is not None:
            self._name = name
            self._index(name)
        # Otherwise just check that the tag name or id was provided
        elif not id:
            raise TCMSError("Need either tag id or tag name "
                            "to initialize the Tag object.")

    def __str__(self):
        """ Tag name for printing """
        return self.name

    def __hash__(self):
        """ Use tag name for hashing """
        # This is necessary until BZ#1084301 is fixed
        return hash(self.name)

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  Tag Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _fetch(self, inject=None):
        """ Fetch tag data from the server """
        TCMS._fetch(self, inject)

        # Directly fetch from the initial object dict
        if inject is not None:
            log.debug("Initializing Tag ID#{0}".format(inject["id"]))
            log.data(pretty(inject))
            self._id = inject["id"]
            self._name = inject["name"]
        # Search by tag id
        elif self._id is not TCMSNone:
            try:
                log.info("Fetching tag " + self.identifier)
                inject = self._server.Tag.filter({'pk': self.id})
                log.debug("Initializing tag " + self.identifier)
                log.data(pretty(inject))
                self._inject = inject
                self._name = inject[0]["name"]
            except IndexError:
                raise TCMSError(
                    "Cannot find tag for {0}".format(self.identifier))
        # Search by tag name
        else:
            try:
                log.info("Fetching tag '{0}'".format(self.name))
                inject = self._server.Tag.filter({'name': self.name})
                log.debug("Initializing tag '{0}'".format(self.name))
                log.data(pretty(inject))
                self._inject = inject
                self._id = inject[0]["id"]
            except IndexError:
                raise TCMSError(
                    "Cannot find tag '{0}'".format(self.name))
        # Index the fetched object into cache
        self._index(self.name)


# We need to import mutable here because of cyclic import
from tcms_api.mutable import TestCase, TestCaseRun  # noqa: E402
