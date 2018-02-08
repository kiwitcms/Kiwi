# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
#   Copyright (c) 2018 Kiwi TCMS project. All rights reserved.
#   Author: Alexander Todorov <info@kiwitcms.org>
#
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
Mutable TCMS objects
"""

import datetime
from pprint import pformat as pretty

import tcms_api.config as config

from tcms_api.config import log
from tcms_api.base import TCMS, TCMSNone, _getter, _setter
from tcms_api.xmlrpc import TCMSError
from tcms_api.immutable import (Build, CaseStatus, Category,
                                PlanType, Priority, Product, TestCaseRunStatus, Tag, User, Version)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Mutable Class
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class Mutable(TCMS):
    """
    General class for all mutable TCMS objects.

    Provides the update() method which pushes the changes (if any
    happened) to the TCMS server and the _update() method performing
    the actual update (to be implemented by respective class).
    """

    # Default expiration for mutable objects is 1 hour
    _expiration = datetime.timedelta(hours=1)

    def __init__(self, id=None, prefix="ID"):
        """ Initially set up to unmodified state """
        self._modified = False
        TCMS.__init__(self, id, prefix)

    def _update(self):
        """ Save data to server (to be implemented by respective class) """
        raise TCMSError("Data update not implemented")

    def update(self):
        """ Update the data, if modified, to the server """
        if self._modified:
            self._update()
            self._modified = False
            # Data are now in sync with the server
            self._fetched = datetime.datetime.now()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestPlan Class
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
    _attributes = ["author", "children", "name",
                   "owner", "parent", "product", "is_active", "tags", "testcases",
                   "testruns", "type", "version"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TestPlan Properties
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # Read-only properties
    id = property(_getter("id"), doc="Test plan id.")
    author = property(_getter("author"), doc="Test plan author.")
    children = property(_getter("children"), doc="Child test plans.")
    tags = property(_getter("tags"), doc="Attached tags.")
    testcases = property(_getter("testcases"),
                         doc="Container with test cases linked to this plan.")
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
    is_active = property(_getter("is_active"), _setter("is_active"),
                         doc="True if Test Plan is active.")
    version = property(_getter("version"), _setter("version"),
                       doc="Default product version.")

    @property
    def synopsis(self):
        """ One line test plan overview """
        return "{0} - {1} ({2} cases, {3} runs)".format(
               self.identifier,
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
    #  TestPlan Special
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
        if initialized:
            return
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
            raise TCMSError(
                "Need either id or name, product, version "
                "and type to initialize the test plan")

    def __iter__(self):
        """ Provide test cases as the default iterator """
        for testcase in self.testcases:
            yield testcase

    def __str__(self):
        """ Test plan id & summary for printing """
        return "{0} - {1}".format(self.identifier, self.name)

    @staticmethod
    def search(**query):
        """ Search for test plans """
        return [TestPlan(hash)
                for hash in TCMS()._server.TestPlan.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TestPlan Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, name, product, version, type, **kwargs):
        """ Create a new test plan """

        hash = {}

        # Name
        if name is None:
            raise TCMSError("Name required for creating new test plan")
        hash["name"] = name

        # Product
        if product is None:
            raise TCMSError("Product required for creating new test plan")
        elif isinstance(product, (int, str)):
            product = Product(product)
        hash["product"] = product.id

        # Version
        if version is None:
            raise TCMSError("Version required for creating new test plan")
        elif isinstance(version, int):
            version = Version(version)
        elif isinstance(version, str):
            version = Version(name=version, product=product)
        hash["default_product_version"] = version.id

        # Type
        if type is None:
            raise TCMSError("Type required for creating new test plan")
        elif isinstance(type, (int, str)):
            type = PlanType(type)
        hash["type"] = type.id

        # Parent
        parent = kwargs.get("parent")
        if parent is not None:
            if isinstance(parent, int):
                parent = TestPlan(parent)
            hash["parent"] = parent.id

        # Document - if not explicitly specified, put empty text
        hash["text"] = kwargs.get("text", " ")

        # Workaround for BZ#725995
        hash["is_active"] = "1"

        # Submit
        log.info("Creating a new test plan")
        log.data(pretty(hash))
        inject = self._server.TestPlan.create(hash)
        log.data(pretty(inject))
        try:
            self._id = inject["plan_id"]
        except TypeError:
            log.debug("Failed to create a new test plan")
            log.data(pretty(hash))
            log.data(pretty(inject))
            raise TCMSError("Failed to create test plan")
        self._fetch(inject)
        log.info("Successfully created {0}".format(self))

    def _fetch(self, inject=None):
        """ Initialize / refresh test plan data.

        Either fetch them from the server or use provided hash.
        """
        TCMS._fetch(self, inject)

        # Fetch the data hash from the server unless provided
        if inject is None:
            log.info("Fetching test plan " + self.identifier)
            try:
                inject = self._server.TestPlan.filter({'pk': self.id})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError(
                    "Failed to fetch test plan TP#{0}".format(self.id))
            self._inject = inject
        # Otherwise just initialize the id from inject
        else:
            self._id = inject["plan_id"]
        log.debug("Initializing test plan " + self.identifier)
        log.data(pretty(inject))
        if "plan_id" not in inject:
            log.data(pretty(inject))
            raise TCMSError("Failed to initialize " + self.identifier)

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
        self._is_active = inject["is_active"] in ["True", True]
        if inject["parent_id"] is not None:
            self._parent = TestPlan(inject["parent_id"])
        else:
            self._parent = None

        # Initialize containers
        self._testcases = PlanCases(self)
        self._testruns = PlanRuns(self)
        self._children = ChildPlans(self)
        # If all tags are cached, initialize them directly from the inject
        if "tag" in inject and Tag._is_cached(inject["tag"]):
            self._tags = PlanTags(
                self, inset=[Tag(tag) for tag in inject["tag"]])
        else:
            self._tags = PlanTags(self)

        # Index the fetched object into cache
        self._index()

    def _update(self):
        """ Save test plan data to the server """

        # Prepare the update hash
        hash = {}
        hash["name"] = self.name
        hash["product"] = self.product.id
        hash["type"] = self.type.id
        hash["is_active"] = self._is_active
        if self.parent is not None:
            hash["parent"] = self.parent.id
        hash["default_product_version"] = self.version.id
        if self.owner is not None:
            hash["owner"] = self.owner.id

        log.info("Updating test plan " + self.identifier)
        log.data(pretty(hash))
        self._server.TestPlan.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._tags is not TCMSNone:
            self.tags.update()
        if self._testcases is not TCMSNone:
            self.testcases.update()
        if self._testruns is not TCMSNone:
            self.testruns.update()
        if self._children is not TCMSNone:
            self.children.update()

        # Update self (if modified)
        Mutable.update(self)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestRun Class
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
    _attributes = ["build", "caseruns", "finished", "manager",
                   "notes", "product", "started", "summary", "tags",
                   "tester", "testcases", "testplan", "time"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TestRun Properties
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
                        doc="TestCaseRun objects related to this test run.")
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
    summary = property(_getter("summary"), _setter("summary"),
                       doc="Test run summary.")
    tester = property(_getter("tester"), _setter("tester"),
                      doc="Default tester.")
    time = property(_getter("time"), _setter("time"),
                    doc="Estimated time.")

    @property
    def synopsis(self):
        """ One-line test run overview """
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
    #  TestRun Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, testplan=None, **kwargs):
        """ Initialize a test run or create a new one.

        Initialize an existing test run if id provided, otherwise create
        a new test run based on specified test plan (required). Other
        parameters are optional and have the following defaults:

            build ....... "unspecified"
            product ..... test run product
            version ..... test run product version
            summary ..... <test plan name> on <build>
            notes ....... ""
            manager ..... current user
            tester ...... current user
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id)
        if initialized:
            return
        Mutable.__init__(self, id, prefix="TR")

        # If inject given, fetch test case data from it
        if inject:
            self._fetch(inject)
        # Create a new test run based on provided plan
        elif testplan:
            self._create(testplan=testplan, **kwargs)
        # Otherwise just check that the test run id was provided
        elif not id:
            raise TCMSError(
                "Need either id or test plan to initialize the test run")

    def __iter__(self):
        """ Provide test case runs as the default iterator """
        for caserun in self.caseruns:
            yield caserun

    def __str__(self):
        """ Test run id & summary for printing """
        return "{0} - {1}".format(self.identifier, self.summary)

    @staticmethod
    def search(**query):
        """ Search for test runs """
        return [TestRun(hash)
                for hash in TCMS()._server.TestRun.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TestRun Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, testplan, product=None, version=None, build=None,
                summary=None, notes=None, manager=None, tester=None, **kwargs):
        """ Create a new test run """

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

        # Build
        if build is None:
            build = "unspecified"
        if isinstance(build, str):
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

        # Submit to the server and initialize
        log.info("Creating a new test run based on {0}".format(testplan))
        log.data(pretty(hash))
        testrunhash = self._server.TestRun.create(hash)
        log.data(pretty(testrunhash))
        try:
            self._id = testrunhash["run_id"]
        except TypeError:
            log.debug("Failed to create a new test run based on {0}".format(
                      testplan))
            log.data(pretty(hash))
            log.data(pretty(testrunhash))
            raise TCMSError("Failed to create test run")
        self._fetch(testrunhash)
        # Add newly created test run to testplan.testruns container
        if PlanRuns._is_cached(testplan.testruns):
            testplan.testruns._fetch(list(testplan.testruns) + [self])
        log.info("Successfully created {0}".format(self))

    def _fetch(self, inject=None):
        """ Initialize / refresh test run data.

        Either fetch them from the server or use the provided hash.
        """
        TCMS._fetch(self, inject)

        # Fetch the data hash from the server unless provided
        if inject is None:
            log.info("Fetching test run {0}".format(self.identifier))
            try:
                inject = self._server.TestRun.filter({'pk': self.id})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError(
                    "Failed to fetch test run TR#{0}".format(self.id))
            self._inject = inject
        else:
            self._id = inject["run_id"]
        log.debug("Initializing test run {0}".format(self.identifier))
        log.data(pretty(inject))

        # Set up attributes
        self._build = Build(inject["build_id"])
        self._manager = User(inject["manager_id"])
        self._notes = inject["notes"]
        self._summary = inject["summary"]
        self._tester = User(inject["default_tester_id"])
        self._testplan = TestPlan(inject["plan_id"])
        self._time = inject["estimated_time"]
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
        self._tags = RunTags(self)

        # Index the fetched object into cache
        self._index()

    def _update(self):
        """ Save test run data to the server """

        # Prepare the update hash
        hash = {}
        hash["build"] = self.build.id
        hash["default_tester"] = self.tester.id
        hash["estimated_time"] = self.time
        hash["manager"] = self.manager.id
        hash["notes"] = self.notes
        # This is required until BZ#731982 is fixed
        hash["product"] = self.build.product.id
        hash["summary"] = self.summary

        log.info("Updating test run " + self.identifier)
        log.data(pretty(hash))
        self._server.TestRun.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._tags is not TCMSNone:
            self.tags.update()
        if self._caseruns is not TCMSNone:
            self._caseruns.update()
        if self._testcases is not TCMSNone:
            self._testcases.update()

        # Update self (if modified)
        Mutable.update(self)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestCase Class
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
    _attributes = ["action", "arguments", "author", "automated",
                   "autoproposed", "breakdown", "bugs", "category", "components",
                   "created", "effect", "link", "manual", "notes", "plans",
                   "priority", "script", "setup", "status", "summary",
                   "tags", "tester", "testplans", "time"]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TestCase Properties
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
    setup = property(_getter("setup"),
                     doc="Setup steps to prepare the machine for the test case.")
    action = property(_getter("action"),
                      doc="Actions to be performed.")
    effect = property(_getter("effect"),
                      doc="Expected Results to be measured.")
    breakdown = property(_getter("breakdown"),
                         doc="Breakdown steps to return machine to original state.")

    @property
    def synopsis(self):
        """ Short summary about the test case """
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
    #  TestCase Special
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
        if initialized:
            return
        Mutable.__init__(self, id, prefix="TC")

        # If inject given, fetch test case data from it
        if inject:
            self._fetch(inject)
        # Create a new test case based on summary and category
        elif summary and category:
            self._create(summary=summary, category=category, **kwargs)
        # Otherwise just check that the test case id was provided
        elif not id:
            raise TCMSError("Need either id or both summary and category "
                            "to initialize the test case")

    def __str__(self):
        """ Test case id & summary for printing """
        return "{0} - {1}".format(self.identifier, self.summary)

    @staticmethod
    def search(**query):
        """ Search for test cases """
        # Special handling for automated & manual attributes
        manual = automated = None
        if "automated" in query:
            automated = query["automated"]
            del query["automated"]
        if "manual" in query:
            manual = query["manual"]
            del query["manual"]
        # Map to appropriate value of 'is_automated' attribute
        if manual is not None or automated is not None:
            if automated is False and manual is False:
                raise TCMSError("Invalid search "
                                "('manual' and 'automated' cannot be both False)")
            elif automated is False:
                query["is_automated"] = 0
            elif manual is False:
                query["is_automated"] = 1
            elif automated is True and manual is True:
                query["is_automated"] = 2
            elif automated is True:
                query["is_automated__in"] = [1, 2]
            elif manual is True:
                query["is_automated__in"] = [0, 2]
        log.debug("Searching for test cases")
        log.data(pretty(query))
        return [TestCase(inject)
                for inject in TCMS()._server.TestCase.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TestCase Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, summary, category, **kwargs):
        """ Create a new test case """

        hash = {}

        # Summary
        hash["summary"] = summary

        # If category provided as text, we need product as well
        product = kwargs.get("product")
        if isinstance(category, str) and not kwargs.get("product"):
            raise TCMSError(
                "Need product when category specified by name")
        # Category & Product
        if isinstance(category, str):
            category = Category(category=category, product=product)
        elif not isinstance(category, Category):
            raise TCMSError("Invalid category '{0}'".format(category))
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
            if isinstance(tester, str):
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
            if isinstance(status, str):
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
        hash["estimated_time"] = kwargs.get("time", '00:00:00')

        # Notes
        notes = kwargs.get("notes")
        if notes:
            hash["notes"] = notes

        # Submit
        log.info("Creating a new test case")
        log.data(pretty(hash))
        testcasehash = self._server.TestCase.create(hash)
        log.data(pretty(testcasehash))
        try:
            self._id = testcasehash["case_id"]
        except TypeError:
            log.debug("Failed to create a new test case")
            log.data(pretty(hash))
            log.data(pretty(testcasehash))
            raise TCMSError("Failed to create test case")
        self._fetch(testcasehash)
        log.info("Successfully created {0}".format(self))

    def _fetch(self, inject=None):
        """ Initialize / refresh test case data.

        Either fetch them from the server or use provided hash.
        """
        TCMS._fetch(self, inject)

        # Fetch the data hash from the server unless provided
        if inject is None:
            log.info("Fetching test case " + self.identifier)
            try:
                inject = self._server.TestCase.filter({'pk': self.id})[0]
            except IndexError as error:
                log.debug(error)
                raise TCMSError(
                    "Failed to fetch test case TC#{0}".format(self.id))
            self._inject = inject
        else:
            self._id = inject["case_id"]
        log.debug("Initializing test case " + self.identifier)
        log.data(pretty(inject))

        # Set up attributes
        self._arguments = inject["arguments"]
        self._author = User(inject["author_id"])
        self._category = Category(inject["category_id"])
        if isinstance(inject["create_date"], str):
            self._created = datetime.datetime.strptime(
                inject["create_date"], "%Y-%m-%d %H:%M:%S")
        else:
            self._created = inject["create_date"]
        self._link = inject["extra_link"]
        self._notes = inject["notes"]
        self._priority = Priority(inject["priority_id"])
        self._requirement = inject["requirement"]
        self._script = inject["script"]
        self._status = CaseStatus(inject["case_status_id"])
        self._summary = inject["summary"]
        self._time = inject["estimated_time"]
        if inject["default_tester_id"] is not None:
            self._tester = User(inject["default_tester_id"])
        else:
            self._tester = None

        # Handle manual, automated and autoproposed
        self._automated = inject["is_automated"] in [1, '1', 2, '2']
        self._manual = inject["is_automated"] in [0, '0', 2, '2']
        self._autoproposed = inject["is_automated_proposed"]

        # Empty script or arguments to be handled same as None
        if self._script == "":
            self._script = None
        if self._arguments == "":
            self._arguments = None

        # Test case documentation
        for attribute in ["setup", "action", "effect", "breakdown"]:
            if "text" in inject:
                setattr(self, "_" + attribute, inject["text"][attribute])
            else:
                setattr(self, "_" + attribute, None)

        # Initialize containers
        self._bugs = CaseBugs(self)
        self._testplans = CasePlans(self)
        self._components = CaseComponents(self)
        # If all tags are cached, initialize them directly from the inject
        if "tag" in inject and Tag._is_cached(inject["tag"]):
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
        hash["summary"] = self.summary
        if self.tester:
            hash["default_tester"] = self.tester.login

        log.info("Updating test case " + self.identifier)
        log.data(pretty(hash))
        self._server.TestCase.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._bugs is not TCMSNone:
            self.bugs.update()
        if self._tags is not TCMSNone:
            self.tags.update()
        if self._testplans is not TCMSNone:
            self.testplans.update()
        if self._components is not TCMSNone:
            self._components.update()

        # Update self (if modified)
        Mutable.update(self)


class TestCaseRun(Mutable):
    """
    Test case run.

    Provides case run attributes such as status and assignee, including
    the relevant 'testcase' object.
    """

    _identifier_width = 8

    # By default we do not cache TestCaseRun objects at all
    _expiration = config.NEVER_CACHE
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
                        doc="Test case object.")
    testrun = property(_getter("testrun"),
                       doc="Test run object.")
    bugs = property(_getter("bugs"),
                    doc="Attached bugs.")

    # Read-write properties
    assignee = property(_getter("assignee"), _setter("assignee"),
                        doc="Test case run assignee object.")
    build = property(_getter("build"), _setter("build"),
                     doc="Test case run build object.")
    notes = property(_getter("notes"), _setter("notes"),
                     doc="Test case run notes (string).")
    sortkey = property(_getter("sortkey"), _setter("sortkey"),
                       doc="Test case sort key (int).")
    status = property(_getter("status"), _setter("status"),
                      doc="Test case run status object.")

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
    #  Special
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __init__(self, id=None, testcase=None, testrun=None, **kwargs):
        """ Initialize a test case run or create a new one.

        Initialize an existing test case run (if id provided) or create
        a new test case run (based on provided test case and test run).
        """

        # Initialize (unless already done)
        id, name, inject, initialized = self._is_initialized(id, **kwargs)
        if initialized:
            return
        Mutable.__init__(self, id, prefix="CR")

        # If inject given, fetch test case run data from it
        if inject:
            self._fetch(inject, **kwargs)
        # Create a new test case run based on case and run
        elif testcase and testrun:
            self._create(testcase=testcase, testrun=testrun, **kwargs)
        # Otherwise just check that the test case run id was provided
        elif not id:
            raise TCMSError("Need either id or testcase and testrun "
                            "to initialize the case run")

    def __str__(self):
        """ Case run id, status & summary for printing """
        return "{0} - {1} - {2}".format(
            self.status.shortname, self.identifier, self.testcase.summary)

    @staticmethod
    def search(**query):
        """ Search for case runs """
        return [TestCaseRun(inject) for inject in
                TCMS()._server.TestCaseRun.filter(dict(query))]

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #  TestCaseRun Methods
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _create(self, testcase, testrun, **kwargs):
        """ Create a new case run """

        hash = {}

        # TestCase
        if testcase is None:
            raise TCMSError("Case ID required for new case run")
        elif isinstance(testcase, str):
            testcase = TestCase(testcase)
        hash["case"] = testcase.id

        # TestRun
        if testrun is None:
            raise TCMSError("Run ID required for new case run")
        elif isinstance(testrun, str):
            testrun = TestRun(testrun)
        hash["run"] = testrun.id

        # Build is required by XMLRPC
        build = testrun.build
        hash["build"] = build.id

        # Submit
        log.info("Creating new case run")
        log.data(pretty(hash))
        inject = self._server.TestCaseRun.create(hash)
        log.data(pretty(inject))
        try:
            self._id = inject["case_run_id"]
        except TypeError:
            log.debug("Failed to create new case run")
            log.data(pretty(hash))
            log.data(pretty(inject))
            raise TCMSError("Failed to create case run")
        self._fetch(inject)
        log.info("Successfully created {0}".format(self))

        # And finally add to testcases and caseruns containers
        self.testrun.testcases._fetch(
            [self.testcase] + list(self.testrun.testcases))
        self.testrun.caseruns._fetch(
            [self] + list(self.testrun.caseruns))

    def _fetch(self, inject=None, **kwargs):
        """ Initialize / refresh test case run data.

        Either fetch them from the server or use the supplied hashes.
        """
        TCMS._fetch(self, inject)

        # Fetch the data from the server unless inject provided
        if inject is None:
            log.info("Fetching case run {0}".format(self.identifier))
            inject = self._server.TestCaseRun.filter({'pk': self.id})[0]
            self._inject = inject
        else:
            self._id = inject["case_run_id"]
        log.debug("Initializing case run {0}".format(self.identifier))
        log.data(pretty(inject))

        # Set up attributes
        self._assignee = User(inject["assignee_id"])
        self._build = Build(inject["build_id"])
        self._notes = inject["notes"]
        if inject["sortkey"] is not None:
            self._sortkey = int(inject["sortkey"])
        else:
            self._sortkey = None
        self._status = TestCaseRunStatus(inject["case_run_status_id"])
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
        """ Save test case run data to the server """

        # Prepare the update hash
        hash = {}
        hash["build"] = self.build.id
        hash["assignee"] = self.assignee.id
        hash["case_run_status"] = self.status.id
        hash["notes"] = self.notes
        hash["sortkey"] = self.sortkey
        # Work around BZ#715596
        if self.notes is None:
            hash["notes"] = ""
        log.info("Updating case run " + self.identifier)
        log.data(pretty(hash))
        self._server.TestCaseRun.update(self.id, hash)

    def update(self):
        """ Update self and containers, if modified, to the server """

        # Update containers (if initialized)
        if self._bugs is not TCMSNone:
            self.bugs.update()

        # Update self (if modified)
        Mutable.update(self)


# We need to import containers here because of cyclic import
from tcms_api.containers import (
    CaseBugs, CaseComponents, CasePlans,
    CaseRunBugs, CaseTags, ChildPlans, PlanCases,
    PlanRuns, PlanTags, RunCaseRuns, RunCases, RunTags)  # noqa: E402
