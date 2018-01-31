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

import unittest

from tcms_api.utils import *       # noqa: F403
from tcms_api.config import *      # noqa: F403
from tcms_api.base import *        # noqa: F403
from tcms_api.immutable import *   # noqa: F403
from tcms_api.mutable import *     # noqa: F403
from tcms_api.containers import *  # noqa: F403

from tcms_api.tests import BaseAPIClient_TestCase

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Utils
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class UtilsTests(unittest.TestCase):
    """ Tests for utility functions """

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
        original = Logging.get()
        for level in [log.DEBUG, log.WARN, log.ERROR]:
            set_log_level(level)
            self.assertEqual(Logging.get(), level)
            self.assertEqual(get_log_level(), level)
        Logging.set(original)

    def test_get_set_cache_level(self):
        """ Get & set the caching level """
        original = Caching().get()
        for level in [CACHE_NONE, CACHE_OBJECTS]:
            set_cache_level(level)
            self.assertEqual(Caching().get(), level)
            self.assertEqual(get_cache_level(), level)
        Caching().set(original)

    def test_get_set_color_mode(self):
        """ Get & set the color mode """
        original = Coloring().get()
        for mode in [COLOR_ON, COLOR_OFF, COLOR_AUTO]:
            set_color_mode(mode)
            self.assertEqual(Coloring().get(), mode)
            self.assertEqual(get_color_mode(), mode)
        Coloring().set(original)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Build
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class BuildTests(BaseAPIClient_TestCase):
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

    def test_invalid_build_id(self):
        """ Invalid build id should raise exception """
        def fun():
            return Build(-1).name
        self.assertRaises(TCMSError, fun)

    def test_invalid_build_name(self):
        """ Invalid build name should raise exception """
        def fun():
            return Build(name="bbbad-bbbuild", product=self.product.name).id
        self.assertRaises(TCMSError, fun)

    def test_cache_none(self):
        """ Cache none """
        set_cache_level(CACHE_NONE)
        build1 = Build(self.build.id)
        self.assertEqual(build1.name, self.build.name)

        requests = TCMS._requests
        build2 = Build(self.build.id)
        self.assertEqual(build2.name, self.build.name)
        self.assertEqual(build1, build2)
        self.assertEqual(TCMS._requests, requests + 1)

    def test_cache_objects(self):
        """ Cache objects """
        Build._cache = {}  # clear cache
        set_cache_level(CACHE_OBJECTS)

        build1 = Build(self.build.id)
        self.assertEqual(build1.name, self.build.name)

        requests = TCMS._requests
        build2 = Build(self.build.id)
        self.assertEqual(build2.name, self.build.name)
        self.assertEqual(build1, build2)
        self.assertEqual(id(build1), id(build2))
        self.assertEqual(TCMS._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Category
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CategoryTests(BaseAPIClient_TestCase):
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
        Category._cache = {}  # clear cache
        set_cache_level(CACHE_OBJECTS)

        # The first round (fetch category data from server)
        category = Category(self.category.id)
        self.assertEqual(category.name, self.category.name)

        # The second round (there should be no more requests)
        requests = TCMS._requests
        category = Category(self.category.id)
        self.assertEqual(category.name, self.category.name)
        self.assertEqual(TCMS._requests, requests)

    def test_cache_none(self):
        """ Cache none """
        set_cache_level(CACHE_NONE)

        # The first round (fetch category data from server)
        category = Category(self.category.id)
        self.assertEqual(category.name, self.category.name)

        # The second round (there should be another request)
        requests = TCMS._requests
        category = Category(self.category.id)
        self.assertEqual(category.name, self.category.name)
        self.assertEqual(TCMS._requests, requests + 1)

    def test_invalid_category(self):
        """ Invalid category should raise exception """
        def fun():
            Category(category="Bad", product=self.product.name).id
        original_log_level = get_log_level()
        set_log_level(log.CRITICAL)
        self.assertRaises(TCMSError, fun)
        set_log_level(original_log_level)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanType
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanTypeTests(BaseAPIClient_TestCase):
    def test_invalid_type(self):
        """ Invalid plan type should raise exception """
        def fun():
            PlanType(name="Bad Plan Type").id
        original_log_level = get_log_level()
        set_log_level(log.CRITICAL)
        self.assertRaises(TCMSError, fun)
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
        PlanType._cache = {}  # clear cache
        set_cache_level(CACHE_OBJECTS)

        # The first round (fetch plantype data from server)
        plantype1 = PlanType(self.plantype.id)
        self.assertTrue(isinstance(plantype1.name, str))

        # The second round (there should be no more requests)
        requests = TCMS._requests
        plantype2 = PlanType(self.plantype.id)
        self.assertTrue(isinstance(plantype2.name, str))
        self.assertEqual(TCMS._requests, requests)

        # The third round (fetching by plan type name)
        plantype3 = PlanType(self.plantype.name)
        self.assertTrue(isinstance(plantype3.id, int))
        self.assertEqual(TCMS._requests, requests)

        # All plan types should point to the same object
        self.assertEqual(id(plantype1), id(plantype2))
        self.assertEqual(id(plantype1), id(plantype3))

    def test_cache_none(self):
        """ Cache none """
        set_cache_level(CACHE_NONE)

        # The first round (fetch plantype data from server)
        plantype1 = PlanType(self.plantype.id)
        self.assertTrue(isinstance(plantype1.name, str))

        # The second round (there should be another request)
        requests = TCMS._requests
        plantype2 = PlanType(self.plantype.id)
        self.assertTrue(isinstance(plantype2.name, str))
        self.assertEqual(TCMS._requests, requests + 1)

        # The third round (fetching by plan type name)
        plantype3 = PlanType(self.plantype.name)
        self.assertTrue(isinstance(plantype3.id, int))
        self.assertEqual(TCMS._requests, requests + 2)

        # Plan types should be different objects in memory
        self.assertNotEqual(id(plantype1), id(plantype2))
        self.assertNotEqual(id(plantype1), id(plantype3))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Product
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class ProductTests(BaseAPIClient_TestCase):

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

    def test_cache_none(self):
        """ Test caching in Product class """
        set_cache_level(CACHE_NONE)

        product = Product(self.product.id)
        self.assertEqual(product.name, self.product.name)

        requests = TCMS._requests
        product = Product(self.product.id)
        self.assertEqual(product.name, self.product.name)
        self.assertEqual(TCMS._requests, requests + 1)

    def test_cache_objects(self):
        Product._cache = {}  # clear cache
        set_cache_level(CACHE_OBJECTS)

        product = Product(self.product.id)
        self.assertEqual(product.name, self.product.name)
        requests = TCMS._requests

        product = Product(self.product.id)
        self.assertEqual(product.name, self.product.name)
        self.assertEqual(TCMS._requests, requests)

    def testProductAdvancedCachingID(self):
        """ Advanced caching (init by ID) """
        requests = TCMS._requests
        Product._cache = {}
        # Turn off caching
        set_cache_level(CACHE_NONE)
        product = Product(self.product.id)
        log.info(product.name)
        product2 = Product(self.product.name)
        log.info(product2.id)
        self.assertEqual(TCMS._requests, requests + 2)
        self.assertNotEqual(id(product), id(product2))
        # Turn on caching
        Product._cache = {}
        set_cache_level(CACHE_OBJECTS)
        product = Product(self.product.id)
        log.info(product.name)
        product2 = Product(self.product.name)
        log.info(product2.id)
        self.assertEqual(TCMS._requests, requests + 3)
        self.assertEqual(id(product), id(product2))

    def testProductAdvancedCachingName(self):
        """ Advanced caching (init by name) """
        requests = TCMS._requests
        Product._cache = {}
        # Turn off caching
        set_cache_level(CACHE_NONE)
        product = Product(self.product.name)
        log.info(product.id)
        product2 = Product(self.product.id)
        log.info(product2.name)
        self.assertEqual(TCMS._requests, requests + 2)
        self.assertNotEqual(id(product), id(product2))
        # Turn on caching
        Product._cache = {}
        set_cache_level(CACHE_OBJECTS)
        product = Product(self.product.name)
        log.info(product.id)
        product2 = Product(self.product.id)
        log.info(product2.name)
        self.assertEqual(TCMS._requests, requests + 3)
        self.assertEqual(id(product), id(product2))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  User
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class UserTests(BaseAPIClient_TestCase):
    def test_no_name(self):
        """ User with no name set in preferences """
        user = User()
        user._name = None
        self.assertEqual(str(user), "No Name")

    def test_current_user(self):
        """ Current user available & sane """
        user = User()
        for data in [user.login, user.email]:
            self.assertTrue(isinstance(data, str))
        self.assertTrue(isinstance(user.id, int))

    def test_cache_none(self):
        """ Cache none """
        set_cache_level(CACHE_NONE)
        User._cache = {}

        requests = TCMS._requests
        # Initialize the same user by id, login and email
        user1 = User(self.api_user.pk)
        user2 = User(self.api_user.username)
        user3 = User(self.api_user.email)
        # User data should be the same.
        # NOTE: _fetch is called when trying to access property that
        # isn't initialized so we assert the requests numbers after
        # this loop!!!
        for user in [user1, user2, user3]:
            self.assertEqual(user.id, self.api_user.pk)
            self.assertEqual(user.login, self.api_user.username)
            self.assertEqual(user.email, self.api_user.email)
        # Three requests to the server should be performed
        self.assertEqual(TCMS._requests, requests + 3)

        # Users should be different objects in memory
        self.assertNotEqual(id(user1), id(user2))
        self.assertNotEqual(id(user1), id(user3))
        self.assertNotEqual(id(user2), id(user3))

    def test_cache_objects(self):
        """ Cache objects """
        User._cache = {}  # clear cache
        set_cache_level(CACHE_OBJECTS)

        # Initialize the same user by id, login and email
        user1 = User(self.api_user.pk)
        # does _fetch()
        self.assertEqual(user1.id, self.api_user.pk)
        self.assertEqual(user1.login, self.api_user.username)
        self.assertEqual(user1.email, self.api_user.email)
        requests = TCMS._requests

        # use cached objects to initialize other instances
        user2 = User(self.api_user.username)
        user3 = User(self.api_user.email)

        # NOTE: _fetch is called when trying to access property that
        # isn't initialized so we assert the requests numbers after
        # this loop!!!
        for user in [user1, user2, user3]:
            self.assertEqual(user.id, self.api_user.pk)
            self.assertEqual(user.login, self.api_user.username)
            self.assertEqual(user.email, self.api_user.email)

        # No other requests to the server should be performed
        self.assertEqual(TCMS._requests, requests)
        # All users objects should be identical
        self.assertEqual(id(user1), id(user2))
        self.assertEqual(id(user1), id(user3))
        self.assertEqual(id(user2), id(user3))

    def test_initialization_by_id(self):
        """ Initializate by id """
        user = User(self.api_user.pk)
        self.assertEqual(user.id, self.api_user.pk)
        self.assertEqual(user.login, self.api_user.username)
        self.assertEqual(user.email, self.api_user.email)

    def test_initialization_by_login(self):
        """ Initializate by login """
        # Check both explicit parameter and autodetection
        user1 = User(login=self.api_user.username)
        user2 = User(self.api_user.username)
        for user in [user1, user2]:
            self.assertEqual(user.id, self.api_user.pk)
            self.assertEqual(user.login, self.api_user.username)
            self.assertEqual(user.email, self.api_user.email)

    def test_initialization_by_email(self):
        """ Initializate by email """
        # Check both explicit parameter and autodetection
        user1 = User(email=self.api_user.email)
        user2 = User(self.api_user.email)
        for user in [user1, user2]:
            self.assertEqual(user.id, self.api_user.pk)
            self.assertEqual(user.login, self.api_user.username)
            self.assertEqual(user.email, self.api_user.email)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Version
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class VersionTests(BaseAPIClient_TestCase):
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

        requests = TCMS._requests
        version = Version(self.version.id)
        self.assertEqual(version.name, self.version.name)
        # Fetches the version twice
        self.assertEqual(TCMS._requests, requests + 1)

    def test_cache_objects(self):
        """ Cache objects """
        Version._cache = {}  # clear cache
        set_cache_level(CACHE_OBJECTS)

        version = Version(self.version.id)
        self.assertEqual(version.name, self.version.name)

        requests = TCMS._requests
        version = Version(self.version.id)
        self.assertEqual(version.name, self.version.name)
        # Should fetch version just once
        self.assertEqual(TCMS._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Component
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class ComponentTests(BaseAPIClient_TestCase):

    def testFetchById(self):
        """ Fetch component by id """
        component = Component(self.component.id)
        self.assertTrue(isinstance(component, Component))
        self.assertEqual(component.name, self.component.name)
        self.assertEqual(component.product.name, self.component.product.name)

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
        set_cache_level(CACHE_OBJECTS)

        # The first round (fetch component data from server)
        requests = TCMS._requests
        component = Component(self.component.id)
        self.assertTrue(isinstance(component.name, str))
        self.assertEqual(TCMS._requests, requests + 1)

        # The second round (there should be no more requests)
        requests = TCMS._requests
        component = Component(self.component.id)
        self.assertTrue(isinstance(component.name, str))
        self.assertEqual(TCMS._requests, requests)

    def testCachingOff(self):
        """ Component caching off """
        # Make sure the cache is empty
        Component._cache = {}
        # Enable cache, remember current number of requests
        set_cache_level(CACHE_NONE)

        requests = TCMS._requests

        # The first round (fetch component data from server)
        component = Component(self.component.id)
        self.assertTrue(isinstance(component.name, str))
        self.assertGreater(TCMS._requests, requests)

        # delete component to cause re-fetch from the server
        del component

        # The second round (there should be another request)
        requests = TCMS._requests
        component = Component(self.component.id)
        self.assertTrue(isinstance(component.name, str))
        self.assertGreater(TCMS._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Tag
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class TagTests(BaseAPIClient_TestCase):
    def setUp(self):
        # re-sets to CACHE_NONE
        super(TagTests, self).setUp()
        self.tag = self.tags[0]

    def test_fetch_by_id(self):
        """ Fetch component by id """
        tag = Tag(self.tag.id)
        self.assertTrue(isinstance(tag, Tag))
        self.assertEqual(tag.name, self.tag.name)

    def test_fetch_by_name(self):
        """ Fetch tag by name """
        for tag in [Tag(name=self.tag.name), Tag(self.tag.name)]:
            self.assertTrue(isinstance(tag, Tag))
            self.assertEqual(tag.id, self.tag.id)

    def test_caching(self):
        """ Tag caching """
        # start caching objects
        Tag._cache = {}  # clear cache
        set_cache_level(CACHE_OBJECTS)

        # First fetch
        tag = Tag(self.tag.id)
        self.assertEqual(tag.name, self.tag.name)

        # verify no request was made to the server
        requests = TCMS._requests
        tag = Tag(self.tag.id)
        self.assertEqual(tag.name, self.tag.name)
        self.assertEqual(requests, TCMS._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestPlan
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class TestPlanTests(BaseAPIClient_TestCase):
    def test_create_invalid(self):
        """ Create a new test plan (missing required parameters) """
        self.assertRaises(TCMSError, TestPlan, name="Test plan")

    def test_create_valid(self):
        """ Create a new test plan (valid) """
        testplan = TestPlan(
            name="Test plan",
            text='Testing',
            type=self.master.type,
            product=self.master.product,
            version=self.master.version)
        self.assertTrue(isinstance(testplan, TestPlan))
        self.assertEqual(testplan.name, "Test plan")

    def test_fetch_nonexistent(self):
        """ Fetch non-existent test plan """
        with self.assertRaises(TCMSError):
            TestPlan(-1).name

    def test_get_by_id(self):
        """ Fetch an existing test plan by id """
        testplan = TestPlan(self.master.id)
        self.assertTrue(isinstance(testplan, TestPlan))
        self.assertEqual(testplan.name, self.master.name)
        self.assertEqual(testplan.type.name, self.master.type.name)
        self.assertEqual(testplan.product.name, self.master.product.name)
        self.assertEqual(testplan.version.name, self.master.version.name)
        self.assertEqual(testplan.owner.login, self.api_user.username)

    def test_plan_status(self):
        """ Test read/write access to the test plan status """
        # Prepare original and negated status
        original = PlanStatus(self.master.status.id)
        negated = PlanStatus(not original.id)
        # Test original value
        testplan = TestPlan(self.master.id)
        self.assertEqual(testplan.status, original)
        testplan.status = negated
        testplan.update()
        del testplan
        # Test negated value
        testplan = TestPlan(self.master.id)
        self.assertEqual(testplan.status, negated)
        testplan.status = original
        testplan.update()
        del testplan
        # Back to the original value
        testplan = TestPlan(self.master.id)
        self.assertEqual(testplan.status, original)

    def test_cache_none(self):
        """ Cache none """
        # Fetch test plan twice ---> two requests
        set_cache_level(CACHE_NONE)

        testplan = TestPlan(self.master.id)
        self.assertEqual(testplan.name, self.master.name)
        requests = TCMS._requests

        # second time
        testplan = TestPlan(self.master.id)
        self.assertEqual(testplan.name, self.master.name)
        self.assertEqual(TCMS._requests, requests + 1)

    def test_cache_objects(self):
        """ Cache objects """
        TestPlan._cache = {}  # clear cache
        # Fetch test plan twice --->  just one request
        set_cache_level(CACHE_OBJECTS)

        testplan = TestPlan(self.master.id)
        self.assertEqual(testplan.name, self.master.name)
        requests = TCMS._requests

        # second time
        testplan = TestPlan(self.master.id)
        self.assertEqual(testplan.name, self.master.name)
        self.assertEqual(TCMS._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestRun
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class TestRunTests(BaseAPIClient_TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        super(TestRunTests, self).setUp()
        self.testcase = self.cases[0]
        self.testrun = self.testruns[0]

    def testCreateInvalid(self):
        """ Create a new test run (missing required parameters) """
        self.assertRaises(TCMSError, TestRun, summary="Test run")

    def testCreateValid(self):
        """ Create a new test run (valid) """
        testrun = TestRun(summary="Test run", testplan=self.master.id)
        self.assertTrue(isinstance(testrun, TestRun))
        self.assertEqual(testrun.summary, "Test run")

    def test_fetch_nonexistent(self):
        """ Fetch non-existent test run """
        with self.assertRaises(TCMSError):
            TestRun(-1).notes

    def testGetById(self):
        """ Fetch an existing test run by id """
        testrun = TestRun(self.testrun.id)
        self.assertTrue(isinstance(testrun, TestRun))
        self.assertEqual(testrun.summary, self.testrun.summary)
        self.assertEqual(testrun.started, self.testrun.started)
        self.assertEqual(testrun.finished, self.testrun.finished)

    def testDisabledCasesOmitted(self):
        """ Disabled test cases should be omitted """
        # Prepare disabled test case
        testcase = TestCase(self.testcase.id)
        original = testcase.status
        testcase.status = CaseStatus("DISABLED")
        testcase.update()
        # Create the test run, make sure the test case is not there
        testrun = TestRun(testplan=self.master.id)
        self.assertTrue(testcase.id not in
                        [caserun.testcase.id for caserun in testrun])
        # Restore the original status
        testcase.status = original
        testcase.update()

    def test_include_only_selected_cases(self):
        """ Include only selected test cases in the new run """
        testcase = TestCase(self.testcase.id)
        testplan = TestPlan(self.master.id)
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

    def test_TestRun_cache_none(self):
        """ Test caching in TestRun class """
        # Turn off caching
        set_cache_level(CACHE_NONE)
        TestRun._cache = {}
        RunTags._cache = {}
        requests = TCMS._requests

        testrun1 = TestRun(self.testrun.id)
        self.assertEqual(testrun1.summary, self.testrun.summary)

        testrun2 = TestRun(self.testrun.id)
        self.assertEqual(testrun2.summary, self.testrun.summary)

        # finally assert there have been 2 more requests to the server
        self.assertEqual(TCMS._requests, requests + 2)

    def test_TestRun_cache_objects(self):
        # Turn on caching
        set_cache_level(CACHE_OBJECTS)
        TestRun._cache = {}
        RunTags._cache = {}

        testrun1 = TestRun(self.testrun.id)
        self.assertEqual(testrun1.summary, self.testrun.summary)
        requests = TCMS._requests

        # try to fetch from cache
        testrun2 = TestRun(self.testrun.id)
        self.assertEqual(testrun2.summary, self.testrun.summary)

        # assert there have been no other requests to the server
        self.assertEqual(TCMS._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestCase
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class TestCaseTests(BaseAPIClient_TestCase):
    def setUp(self):
        super(TestCaseTests, self).setUp()
        self.testcase = self.cases[0]

    def testCreateInvalid(self):
        """ Create a new test case (missing required parameters) """
        self.assertRaises(
            TCMSError, TestCase, summary="Test case summary")

    def testCreateValid(self):
        """ Create a new test case (valid) """
        case = TestCase(summary="Test case summary",
                        product=self.product.name, category=self.category.name)
        self.assertTrue(
            isinstance(case, TestCase), "Check created instance")
        self.assertEqual(case.summary, "Test case summary")
        self.assertEqual(case.priority, Priority("P3"))
        self.assertEqual(str(case.category), self.category.name)

    def testCreateValidWithOptionalFields(self):
        """ Create a new test case, include optional fields """
        # High-priority automated security-related test case
        case = TestCase(
            summary="High-priority automated test case",
            product=self.product,
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
            product=self.product,
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

    def test_fetch_nonexistent(self):
        """ Fetch non-existent test case """
        with self.assertRaises(TCMSError):
            TestCase(-1).summary

    def testGetById(self):
        """ Fetch an existing test case by id """
        testcase = TestCase(self.testcase.id)
        self.assertTrue(isinstance(testcase, TestCase))
        self.assertEqual(testcase.summary, self.testcase.summary)
        self.assertEqual(testcase.category.name, self.testcase.category.name)
        self.assertEqual(testcase.created, self.testcase.created)

    def testGetByInvalidId(self):
        """ Fetch an existing test case by id (invalid id) """
        self.assertRaises(TCMSError, TestCase, 'invalid-id')

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

                # Fetch and update
                testcase = TestCase(self.testcase.id)
                testcase.automated = automated
                testcase.manual = manual
                testcase.update()
                # Reload and check
                testcase = TestCase(self.testcase.id)
                self.assertEqual(testcase.automated, automated)
                self.assertEqual(testcase.manual, manual)

        for autoproposed in [False, True]:
            # Fetch and update
            testcase = TestCase(self.testcase.id)
            testcase.autoproposed = autoproposed
            testcase.update()
            # Reload and check
            testcase = TestCase(self.testcase.id)
            self.assertEqual(testcase.autoproposed, autoproposed)

    def testTestCaseCaching(self):
        """ Test caching in TestCase class """
        requests = TCMS._requests
        # Turn off caching
        set_cache_level(CACHE_NONE)

        testcase1 = TestCase(self.testcase.id)
        testcase2 = TestCase(self.testcase.id)
        # fetch 2 cases
        self.assertEqual(testcase1.summary, self.testcase.summary)
        self.assertEqual(testcase2.summary, self.testcase.summary)

        # assert there have been 2 more requests
        self.assertEqual(TCMS._requests, requests + 2)

        # Turn on caching
        TestCase._cache = {}
        set_cache_level(CACHE_OBJECTS)
        requests = TCMS._requests

        testcase1 = TestCase(self.testcase.id)
        testcase2 = TestCase(self.testcase.id)

        # fetch 2 cases
        self.assertEqual(testcase1.summary, self.testcase.summary)
        self.assertEqual(testcase2.summary, self.testcase.summary)

        # assert only 1 request was made to the server
        self.assertEqual(TCMS._requests, requests + 1)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseComponents
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseComponentsTests(BaseAPIClient_TestCase):
    def setUp(self):
        super(CaseComponentsTests, self).setUp()
        self.testcase = self.cases[0]

    def test1(self):
        """ Unlinking a component from a test case """
        testcase = TestCase(self.testcase.id)
        component = Component(self.component.id)
        testcase.components.remove(component)
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(component not in testcase.components)

    def test2(self):
        """ Linking a component to a test case """
        testcase = TestCase(self.testcase.id)
        component = Component(self.component.id)
        testcase.components.add(component)
        testcase.update()

        # Check server content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(component in testcase.components)

    def test3(self):
        """ Unlinking a component from a test case """
        testcase = TestCase(self.testcase.id)
        component = Component(self.component.id)
        testcase.components.remove(component)
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(component not in testcase.components)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseBugs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseBugsTests(BaseAPIClient_TestCase):
    def setUp(self):
        """ Set up test case from the config """
        super(CaseBugsTests, self).setUp()
        self.testcase = self.cases[0]
        self.bug = Bug(bug=1234)

    def test_bugging1(self):
        """ Detaching bug from a test case """
        # Detach bug and check
        testcase = TestCase(self.testcase.id)
        testcase.bugs.remove(self.bug)
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(self.bug not in testcase.bugs)

    def test_bugging2(self):
        """ Attaching bug to a test case """
        # Attach bug and check
        testcase = TestCase(self.testcase.id)
        testcase.bugs.add(self.bug)
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(self.bug in testcase.bugs)

    def test_bugging3(self):
        """ Detaching bug from a test case """
        # Detach bug and check
        testcase = TestCase(self.testcase.id)
        testcase.bugs.remove(self.bug)
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(self.bug not in testcase.bugs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseRunBugs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseRunBugsTests(BaseAPIClient_TestCase):
    def setUp(self):
        """ Set up test case from the config """
        super(CaseRunBugsTests, self).setUp()
        self.bug = Bug(bug=1234)

    def test_bugging1(self):
        """ Detaching bug from a test case run """
        # Detach bug and check
        caserun = CaseRun(self.caserun.pk)
        caserun.bugs.remove(self.bug)
        caserun.update()
        # Refetch content
        caserun = CaseRun(self.caserun.pk)
        self.assertTrue(self.bug not in caserun.bugs)

    def test_bugging2(self):
        """ Attaching bug to a test case run """
        # Attach bug and check
        caserun = CaseRun(self.caserun.pk)
        caserun.bugs.add(self.bug)
        caserun.update()
        # Refetch content
        caserun = CaseRun(self.caserun.pk)
        self.assertTrue(self.bug in caserun.bugs)

    def test_bugging3(self):
        """ Detaching bug from a test case run """
        # Detach bug and check
        caserun = CaseRun(self.caserun.pk)
        caserun.bugs.remove(self.bug)
        caserun.update()
        # Refetch content
        caserun = CaseRun(self.caserun.pk)
        self.assertTrue(self.bug not in caserun.bugs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanTags
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanTagsTests(BaseAPIClient_TestCase):

    def testTagging1(self):
        """ Untagging a test plan """
        # Remove tag and check
        testplan = TestPlan(self.master.id)
        testplan.tags.remove(Tag("TestTag"))
        testplan.update()
        # Refetch content
        testplan = TestPlan(self.master.id)
        self.assertTrue(Tag("TestTag") not in testplan.tags)

    def testTagging2(self):
        """ Tagging a test plan """
        # Add tag and check
        testplan = TestPlan(self.master.id)
        testplan.tags.add(Tag("TestTag"))
        testplan.update()
        # Refetch content
        testplan = TestPlan(self.master.id)
        self.assertTrue(Tag("TestTag") in testplan.tags)

    def testTagging3(self):
        """ Untagging a test plan """
        # Remove tag and check
        testplan = TestPlan(self.master.id)
        testplan.tags.remove(Tag("TestTag"))
        testplan.update()
        # refetch content
        testplan = TestPlan(self.master.id)
        self.assertTrue(Tag("TestTag") not in testplan.tags)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunTags
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class RunTagsTests(BaseAPIClient_TestCase):
    def setUp(self):
        super(RunTagsTests, self).setUp()
        self.testrun = self.testruns[0]

    def testTagging1(self):
        """ Untagging a test run """
        # Remove tag and check
        testrun = TestRun(self.testrun.id)
        testrun.tags.remove(Tag("TestTag"))
        testrun.update()
        # Refetch content
        testrun = TestRun(self.testrun.id)
        self.assertTrue(Tag("TestTag") not in testrun.tags)

    def testTagging2(self):
        """ Tagging a test run """
        # Add tag and check
        testrun = TestRun(self.testrun.id)
        testrun.tags.add(Tag("TestTag"))
        testrun.update()
        # Refetch content
        testrun = TestRun(self.testrun.id)
        self.assertTrue(Tag("TestTag") in testrun.tags)

    def testTagging3(self):
        """ Untagging a test run """
        # Remove tag and check
        testrun = TestRun(self.testrun.id)
        testrun.tags.remove(Tag("TestTag"))
        testrun.update()
        # Refetch content
        testrun = TestRun(self.testrun.id)
        self.assertTrue(Tag("TestTag") not in testrun.tags)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseTags
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class CaseTagsTests(BaseAPIClient_TestCase):
    def setUp(self):
        super(CaseTagsTests, self).setUp()
        self.testcase = self.cases[0]
        self.tag = self.tags[0]

    def testTagging1(self):
        """ Untagging a test case """
        # Remove tag and check
        testcase = TestCase(self.testcase.id)
        testcase.tags.remove(Tag("TestTag"))
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(Tag("TestTag") not in testcase.tags)

    def testTagging2(self):
        """ Tagging a test case """
        # Add tag and check
        testcase = TestCase(self.testcase.id)
        testcase.tags.add(Tag("TestTag"))
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(Tag("TestTag") in testcase.tags)

    def testTagging3(self):
        """ Untagging a test case """
        # Remove tag and check
        testcase = TestCase(self.testcase.id)
        testcase.tags.remove(Tag("TestTag"))
        testcase.update()
        # Refetch content
        testcase = TestCase(self.testcase.id)
        self.assertTrue(Tag("TestTag") not in testcase.tags)

    def test_string_tags(self):
        """ Support for string tags """
        testcase = TestCase(self.testcase.id)
        # Add string tag
        testcase.tags.add("TestTag")
        testcase.update()
        self.assertTrue("TestTag" in testcase.tags)
        # Remove string tag
        testcase.tags.remove("TestTag")
        testcase.update()
        self.assertTrue("TestTag" not in testcase.tags)

    def test_tagging_with_uncached_tag_by_name(self):
        """ Tagging with uncached tag by name """
        # This tests BZ#1084563, where adding an uncached tag to the container
        # caused the _items() method to fetch the original container content
        # from the server despite the container has been in modified state
        # Make sure the tag is not there
        testcase = TestCase(self.testcase.id)
        testcase.tags.remove(self.tag.name)
        testcase.update()
        # Add tag by name, then immediately check whether it's present
        testcase.tags.add(self.tag.name)
        self.assertTrue(self.tag.name in testcase.tags)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  ChildPlans
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class ChildPlansTests(BaseAPIClient_TestCase):

    def test_add_and_remove_child_plan(self):
        """ Add and remove child test plan """
        parent = TestPlan(self.master.id)
        # Create a new separate plan, make sure it's not child
        child = TestPlan(name="Child test plan", type=parent.type,
                         text='Nothing to document here',
                         product=parent.product, version=parent.version)
        self.assertTrue(child not in parent.children)
        # Add the new test plan to the children, reload, check
        parent.children.add(child)
        parent.update()
        parent = TestPlan(parent.id)
        self.assertTrue(child in parent.children)
        # Remove the child again, update, reload, check
        # FIXME Currently disabled because if BZ#885232
        # parent.children.remove(child)
        # parent.update()
        # parent = TestPlan(parent.id)
        # self.assertTrue(child not in parent.children)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanRuns
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class PlanRunsTests(BaseAPIClient_TestCase):
    def setUp(self):
        super(PlanRunsTests, self).setUp()
        self.testrun = self.testruns[0]

    def test_inclusion(self):
        """ Test run included in the container"""
        testrun = TestRun(self.testrun.id)
        testplan = TestPlan(self.testrun.testplan.id)
        self.assertTrue(testrun in testplan.testruns)

    def test_new_test_run(self):
        """ New test runs should be linked """
        testplan = TestPlan(self.master.id)
        testrun = TestRun(testplan=testplan)
        self.assertTrue(testrun in testplan.testruns)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCases
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class RunCasesTests(BaseAPIClient_TestCase):
    def setUp(self):
        super(RunCasesTests, self).setUp()
        self.testrun = self.testruns[0]
        self.testcase = self.cases[0]

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
        testrun = TestRun(testplan=self.master.id)
        self.assertTrue(testcase in testrun.testcases)
        # Remove and check it's not either in testcases or caseruns
        testrun.testcases.remove(testcase)
        testrun.update()
        self.assertTrue(testcase not in testrun.testcases)
        self.assertTrue(testcase not in
                        [caserun.testcase for caserun in testrun.caseruns])
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
        testrun = TestRun(testrun.id)
        self.assertTrue(testcase in testrun.testcases)
        self.assertTrue(testcase in
                        [caserun.testcase for caserun in testrun.caseruns])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCaseRuns
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


class RunCaseRunsTests(BaseAPIClient_TestCase):
    def setUp(self):
        super(RunCaseRunsTests, self).setUp()
        self.testrun = self.testruns[0]

    def test_present(self):
        """ Check case run presence """
        caserun = CaseRun(self.caserun.pk)
        testrun = TestRun(self.caserun.run_id)
        self.assertTrue(caserun in testrun)

    def test_cases_fetched_just_once_when_cached(self):
        """ Test cases are fetched just once """
        # This test is relevant when caching is turned on
        TestPlan._cache = {}  # clear cache
        TestRun._cache = {}
        set_cache_level(CACHE_OBJECTS)

        testplan = TestPlan(self.master.id)
        testrun = TestRun(self.testrun.id)
        # Make sure plan, run and cases are fetched
        "{0}{1}{2}".format(testplan, testrun, listed(
            [testcase for testcase in testplan]))

        # Now fetching case runs should be a single query to the
        # server because all test cases have already been fetched
        requests = TCMS._requests
        listed([caserun.status for caserun in testrun])
        self.assertEqual(TCMS._requests, requests + 1)
