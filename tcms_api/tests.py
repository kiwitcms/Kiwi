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
Test Suite

For running the unit test suite additional sections are required in the
configuration file. These contain the url of the test server and the
data of existing objects to be tested, for example:

    [test]
    url = https://test.server/xmlrpc/

    [user]
    id = 1234
    login = username
    email = username@example.com

    [product]
    id = 60
    name = Red Hat Enterprise Linux 6

    [version]
    id = 1234
    name = 6.0

    [build]
    id = 12345
    name = RHEL6.6-20140404

    [component]
    id = 123
    name = wget
    product = Red Hat Enterprise Linux 6

    [category]
    id = 123
    name = Integration

    [plantype]
    id = 1
    name = General

    [tag]
    id = 1234
    name = TestTag

    [testplan]
    id = 1234
    name = Test plan
    type = Function
    product = Red Hat Enterprise Linux 6
    version = 6.1
    status = ENABLED
    owner = login

    [testrun]
    id = 6757
    summary = Test Run Summary
    started = 2012-12-12 12:12:12
    finished = None

    [testcase]
    id = 1234
    summary = Test case summary
    product = Red Hat Enterprise Linux 6
    category = Sanity
    created = 2012-12-12 12:12:12

    [caserun]
    id = 123456
    status = PASSED

To exercise the whole test suite run "python -m nitrate.tests". To test
only subset of tests pick the desired classes on the command line:

    python -m nitrate.tests TestCase


Performance tests
~~~~~~~~~~~~~~~~~~

For running the performance test suite an additional section containing
information about the test bed is required:

    [performance]
    testplan = 1234
    testrun = 12345

Use the test-bed-prepare.py script attached in the test directory to
prepare the structure of test plans, test runs and test cases. To run
the performance test suite use --performance command line option.
"""

from __future__ import print_function

import six
import sys
import types
import random
import optparse
import tempfile
import unittest
import datetime

from nitrate.utils import *
from nitrate.cache import *
from nitrate.config import *
from nitrate.base import *
from nitrate.immutable import *
from nitrate.mutable import *
from nitrate.containers import *

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Constants
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Since python 2.7 the test suite results are too verbose
VERBOSE_UNITTEST = sys.version_info >= (2, 7)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Internal Utilities
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _print_time(elapsed_time):
    """ Human readable time format for performance tests """
    converted_time = str(datetime.timedelta(seconds=elapsed_time)).split('.')
    sys.stderr.write("{0} ... ".format(converted_time[0]))

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
        original = Logging.get()
        for level in [log.DEBUG, log.WARN, log.ERROR]:
            set_log_level(level)
            self.assertEqual(Logging.get(), level)
            self.assertEqual(get_log_level(), level)
        Logging.set(original)

    def test_get_set_cache_level(self):
        """ Get & set the caching level """
        original = Caching().get()
        for level in [CACHE_NONE, CACHE_CHANGES, CACHE_OBJECTS]:
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

class BuildTests(unittest.TestCase):
    def setUp(self):
        """ Clear cache, save cache level and initialize test data """
        self.product = config.product
        self.build = config.build
        self.requests = Nitrate._requests
        self.cache_level = get_cache_level()
        cache.clear()

    def tearDown(self):
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

    def test_invalid_build_id(self):
        """ Invalid build id should raise exception """
        fun = lambda: Build(-1).name
        self.assertRaises(NitrateError, fun)

    def test_invalid_build_name(self):
        """ Invalid build name should raise exception """
        fun = lambda: Build(name="bbbad-bbbuild", product=self.product.name).id
        self.assertRaises(NitrateError, fun)

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Category
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CategoryTests(unittest.TestCase):

    def setUp(self):
        """ Clear cache, save cache level and initialize test data """
        cache.clear()
        self.cache_level = get_cache_level()
        self.product = config.product
        self.category = config.category
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanType
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanTypeTests(unittest.TestCase):
    def setUp(self):
        """ Clear cache, save cache level and initialize test data """
        cache.clear()
        self.original_cache_level = get_cache_level()
        self.plantype = config.plantype
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
        self.assertTrue(isinstance(plantype1.name, six.string_types))
        self.assertEqual(Nitrate._requests, self.requests + 1)
        # The second round (there should be no more requests)
        plantype2 = PlanType(self.plantype.id)
        self.assertTrue(isinstance(plantype2.name, six.string_types))
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
        self.assertTrue(isinstance(plantype1.name, six.string_types))
        self.assertEqual(Nitrate._requests, self.requests + 1)
        # The second round (there should be another request)
        plantype2 = PlanType(self.plantype.id)
        self.assertTrue(isinstance(plantype2.name, six.string_types))
        self.assertEqual(Nitrate._requests, self.requests + 2)
        # The third round (fetching by plan type name)
        plantype3 = PlanType(self.plantype.name)
        self.assertTrue(isinstance(plantype3.id, int))
        self.assertEqual(Nitrate._requests, self.requests + 3)
        # Plan types should be different objects in memory
        self.assertNotEqual(id(plantype1), id(plantype2))
        self.assertNotEqual(id(plantype1), id(plantype3))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Product
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ProductTests(unittest.TestCase):
    def setUp(self):
        """ Set up test product from the config """
        self.product = config.product

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  User
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class UserTests(unittest.TestCase):
    def setUp(self):
        """ Clear cache, save cache level and initialize test data """
        cache.clear()
        self.original_cache_level = get_cache_level()
        self.user = config.user
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
            self.assertTrue(isinstance(data, six.string_types))
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Version
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class VersionTests(unittest.TestCase):
    def setUp(self):
        """ Set up version from the config """
        cache.clear()
        self.cache_level = get_cache_level()
        self.version = config.version
        self.product = config.product
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
        cache.save()
        cache.clear()
        cache.load()
        requests = Nitrate._requests
        # Fetch once again ---> no additional request
        version = Version(self.version.id)
        self.assertEqual(version.name, self.version.name)
        self.assertEqual(Nitrate._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Component
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ComponentTests(unittest.TestCase):
    def setUp(self):
        """ Set up component from the config """
        self.component = config.component

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
        self.assertTrue(isinstance(component.name, six.string_types))
        self.assertEqual(Nitrate._requests, requests + 1)
        # The second round (there should be no more requests)
        component = Component(self.component.id)
        self.assertTrue(isinstance(component.name, six.string_types))
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
        self.assertTrue(isinstance(component.name, six.string_types))
        self.assertEqual(Nitrate._requests, requests + 1)
        del component
        # The second round (there should be another request)
        component = Component(self.component.id)
        self.assertTrue(isinstance(component.name, six.string_types))
        self.assertEqual(Nitrate._requests, requests + 2)
        # Restore cache level
        set_cache_level(original)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Tag
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TagTests(unittest.TestCase):
    def setUp(self):
        """ Set up component from the config """
        self.tag = config.tag

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
        # First fetch
        cache.clear()
        tag = Tag(self.tag.id)
        self.assertEqual(tag.name, self.tag.name)
        # Object caching
        if get_cache_level() < CACHE_OBJECTS:
            return
        requests = Nitrate._requests
        tag = Tag(self.tag.id)
        self.assertEqual(tag.name, self.tag.name)
        self.assertEqual(requests, Nitrate._requests)
        # Persistent caching
        if get_cache_level() < CACHE_PERSISTENT:
            return
        cache.save()
        cache.clear()
        cache.load()
        tag = Tag(self.tag.id)
        self.assertEqual(tag.name, self.tag.name)
        self.assertEqual(requests, Nitrate._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestPlan
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestPlanTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan
        self.requests = Nitrate._requests
        self.cache_level = get_cache_level()
        cache.clear()

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

    def test_fetch_nonexistent(self):
        """ Fetch non-existent test plan """
        with self.assertRaises(NitrateError):
            TestPlan(-1).name

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
        cache.save()
        cache.clear()
        cache.load()
        requests = Nitrate._requests
        # Fetch once again ---> no additional request
        testplan = TestPlan(self.testplan.id)
        self.assertEqual(testplan.name, self.testplan.name)
        self.assertEqual(Nitrate._requests, requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestRun
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestRunTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan
        self.testcase = config.testcase
        self.testrun = config.testrun

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

    def test_fetch_nonexistent(self):
        """ Fetch non-existent test run """
        with self.assertRaises(NitrateError):
            TestRun(-1).notes

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  TestCase
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestCaseTests(unittest.TestCase):
    def setUp(self):
        """ Set up test case from the config """
        self.testcase = config.testcase
        self.performance = config.performance

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

    def test_fetch_nonexistent(self):
        """ Fetch non-existent test case """
        with self.assertRaises(NitrateError):
            TestCase(-1).summary

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseRuns
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseRunsTests(unittest.TestCase):
    def setUp(self):
        """ Set up performance test configuration from the config """
        self.performance = config.performance

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CasePlan
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CasePlanTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan
        self.testcase = config.testcase
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
            cache.save()
            cache.clear()
            cache.load()
            caseplan = CasePlan(testcase=testcase, testplan=testplan)
            self.assertEqual(caseplan.sortkey, sortkey)
            self.assertEqual(requests, Nitrate._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseComponents
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseComponentsTests(unittest.TestCase):
    def setUp(self):
        """ Set up component from the config """
        self.component = config.component
        self.testcase = config.testcase

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
        cache.clear()
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
        cache.clear()
        testcase = TestCase(self.testcase.id)
        self.assertTrue(component not in testcase.components)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanComponents
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

'''
Disabled until BZ#866974 is fixed.

class PlanComponentsTests(unittest.TestCase):
    def setUp(self):
        """ Set up component from the config """
        self.component = config.component
        self.testplan = config.testplan

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
        cache.clear()
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
        cache.clear()
        testplan = TestPlan(self.testplan.id)
        self.assertTrue(component not in testplan.components)
'''

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseBugs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseBugsTests(unittest.TestCase):
    def setUp(self):
        """ Set up test case from the config """
        self.testcase = config.testcase
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
        cache.clear()
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
        cache.clear()
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
        cache.clear()
        testcase = TestCase(self.testcase.id)
        self.assertTrue(self.bug not in testcase.bugs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseRunBugs
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseRunBugsTests(unittest.TestCase):
    def setUp(self):
        """ Set up test case from the config """
        self.caserun = config.caserun
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
        cache.clear()
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
        cache.clear()
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
        cache.clear()
        caserun = CaseRun(self.caserun.id)
        self.assertTrue(self.bug not in caserun.bugs)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanTags
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanTagsTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan

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
        cache.clear()
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
        cache.clear()
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
        cache.clear()
        testplan = TestPlan(self.testplan.id)
        self.assertTrue(Tag("TestTag") not in testplan.tags)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunTags
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunTagsTests(unittest.TestCase):
    def setUp(self):
        """ Set up test run from the config """
        self.testrun = config.testrun

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
        cache.clear()
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
        cache.clear()
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
        cache.clear()
        testrun = TestRun(self.testrun.id)
        self.assertTrue(Tag("TestTag") not in testrun.tags)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  CaseTags
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class CaseTagsTests(unittest.TestCase):
    def setUp(self):
        """ Set up test case from the config """
        self.testcase = config.testcase
        self.performance = config.performance
        self.tag = config.tag

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
        cache.clear()
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
        cache.clear()
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
        cache.clear()
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
        cache.clear()
        # Add tag by name, then immediately check whether it's present
        testcase.tags.add(self.tag.name)
        self.assertTrue(self.tag.name in testcase.tags)

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  ChildPlans
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ChildPlansTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanRuns
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanRunsTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan
        self.testrun = config.testrun

    def test_inclusion(self):
        """ Test run included in the container"""
        testplan = TestPlan(self.testplan.id)
        testrun = TestRun(self.testrun.id)
        self.assertTrue(testrun in testplan.testruns)
        # Everything should be kept in the persistent cache
        if get_cache_level() >= CACHE_PERSISTENT:
            cache.save()
            cache.clear()
            cache.load()
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
        if get_cache_level() >= CACHE_PERSISTENT:
            cache.save()
            cache.clear()
            cache.load()
            requests = Nitrate._requests
            testplan = TestPlan(self.testplan.id)
            testrun = TestRun(self.testrun.id)
            self.assertTrue(testrun in testplan.testruns)
            self.assertEqual(requests, Nitrate._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  PlanCasePlans
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class PlanCasePlansTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan
        self.testcase = config.testcase
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
            cache.save()
            cache.clear()
            cache.load()
            testplan = TestPlan(self.testplan.id)
            self.assertEqual(testplan.sortkey(testcase), sortkey)
            self.assertEqual(requests, Nitrate._requests)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCases
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunCasesTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan
        self.testrun = config.testrun
        self.testcase = config.testcase

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
        if get_cache_level() >= CACHE_OBJECTS:
            cache.clear([RunCases, RunCaseRuns])
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
        if get_cache_level() >= CACHE_OBJECTS:
            cache.clear([RunCases, RunCaseRuns])
        testrun = TestRun(testrun.id)
        self.assertTrue(testcase in testrun.testcases)
        self.assertTrue(testcase in
                [caserun.testcase for caserun in testrun.caseruns])

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  RunCaseRuns
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class RunCaseRunsTests(unittest.TestCase):
    def setUp(self):
        """ Set up test plan from the config """
        self.testplan = config.testplan
        self.testrun = config.testrun
        self.caserun = config.caserun

    def test_present(self):
        """ Check case run presence """
        caserun = CaseRun(self.caserun.id)
        testrun = TestRun(self.testrun.id)
        self.assertTrue(caserun in testrun)

    def test_cases_fetched_just_once(self):
        """ Test cases are fetched just once """
        # This test is relevant when caching is turned on
        if get_cache_level() < CACHE_OBJECTS: return
        cache.clear()
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
#  Self Test
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    # Override the server config with the testing instance
    config = Config()
    try:
        config.nitrate = config.test
        print("Testing against {0}".format(config.nitrate.url))
    except AttributeError:
        raise NitrateError("No test server provided in the config file")

    # Use temporary cache file for testing
    temporary_cache = tempfile.NamedTemporaryFile()
    cache = Cache(temporary_cache.name)

    # Parse options
    parser = optparse.OptionParser(
            usage="python nitrate.api [--performance] [class [...]]")
    parser.add_option("--performance",
            action="store_true",
            help="Run performance tests")
    (options, arguments) = parser.parse_args()

    # Custom (more concise) test result class for python 2.7 and newer
    if VERBOSE_UNITTEST:
        class ShortResult(unittest.TextTestResult):
            def getDescription(self, test):
                return test.shortDescription() or str(test)

    # Walk through all unit test classes
    import __main__
    results = {}
    for name in dir(__main__):
        # Pick only unittest classes
        object = getattr(__main__, name)
        if not (isinstance(object, (type, types.ClassType)) and
                issubclass(object, unittest.TestCase)):
            continue
        # Handle test selection on the command line
        name = re.sub("Tests$", "", object.__name__)
        if arguments and name not in arguments:
            continue
        suite = unittest.TestLoader().loadTestsFromTestCase(object)
        # Filter only performance test cases when --performance given
        suite = [case for case in suite
                if options.performance and "performance" in str(case)
                or not options.performance and "performance" not in str(case)]
        if not suite:
            continue
        # Prepare suite, print header and run it
        suite = unittest.TestSuite(suite)
        print(header(name))
        log_level = get_log_level()
        if VERBOSE_UNITTEST:
            results[name] = unittest.TextTestRunner(
                        verbosity=2, resultclass=ShortResult).run(suite)
        else:
            results[name] = unittest.TextTestRunner(verbosity=2).run(suite)
        set_log_level(log_level)

    # Check for failed tests and give a short test summary
    failures = sum([len(result.failures) for result in results.itervalues()])
    errors = sum([len(result.errors) for result in results.itervalues()])
    testsrun = sum([result.testsRun for result in results.itervalues()])
    print(header("Summary"))
    print("{0} tested".format(listed(results, "class", "classes")))
    print("{0} passed".format(listed(testsrun - failures - errors, "test")))
    print("{0} failed".format(listed(failures, "test")))
    print("{0} found".format(listed(errors, "error")))
    if failures:
        print("Failures in: {0}".format(listed([name
                for name, result in results.iteritems()
                if not result.wasSuccessful()])))
