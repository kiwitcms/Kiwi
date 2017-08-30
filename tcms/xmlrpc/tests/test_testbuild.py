# -*- coding: utf-8 -*-

import unittest
from http.client import BAD_REQUEST
from http.client import FORBIDDEN
from http.client import NOT_FOUND

from django.test import TestCase

from tcms.xmlrpc.api import build
from tcms.xmlrpc.tests.utils import make_http_request

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestBuildFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestBuildCreate(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.admin = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin, user_perm='management.add_testbuild')

        cls.staff = UserFactory()
        cls.staff_request = make_http_request(user=cls.staff)

        cls.product = ProductFactory(name='Nitrate')

    @unittest.skip('TODO: fix create to make this test pass.')
    def test_build_create_with_no_args(self):
        bad_args = (self.admin_request, [], (), {})
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.create, self.admin_request, arg)

    def test_build_create_with_no_perms(self):
        self.assertRaisesXmlrpcFault(FORBIDDEN, build.create, self.staff_request, {})

    def test_build_create_with_no_required_fields(self):
        def _create(data):
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.create, self.admin_request, data)

        values = {
            "description": "Test Build",
            "is_active": False
        }
        _create(values)

        values["name"] = "TB"
        _create(values)

        del values["name"]
        values["product"] = self.product.pk
        _create(values)

    @unittest.skip('FIXME: Missing required argument must be handled. 400 is expected.')
    def test_build_create_with_illegal_fields(self):
        values = {
            "product": self.product.pk,
            "name": "B7",
            "milestone": "aaaaaaaa"
        }
        self.assertRaisesXmlrpcFault(BAD_REQUEST, build.create, self.admin_request, values)

    def test_build_create_with_non_exist_product(self):
        values = {
            "product": 9999,
            "name": "B7",
            "description": "Test Build",
            "is_active": False
        }
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.create, self.admin_request, values)

        values['product'] = "AAAAAAAAAA"
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.create, self.admin_request, values)

    def test_build_create_with_chinese(self):
        values = {
            "product": self.product.pk,
            "name": "B99",
            "description": "开源中国",
            "is_active": False
        }
        b = build.create(self.admin_request, values)
        self.assertIsNotNone(b)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertEqual(b['name'], "B99")
        self.assertEqual(b['description'],
                         '\xe5\xbc\x80\xe6\xba\x90\xe4\xb8\xad\xe5\x9b\xbd')
        self.assertEqual(b['is_active'], False)

    def test_build_create(self):
        values = {
            "product": self.product.pk,
            "name": "B7",
            "description": "Test Build",
            "is_active": False
        }
        b = build.create(self.admin_request, values)
        self.assertIsNotNone(b)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertEqual(b['name'], "B7")
        self.assertEqual(b['description'], "Test Build")
        self.assertEqual(b['is_active'], False)


class TestBuildUpdate(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.admin = UserFactory()
        cls.admin_request = make_http_request(user=cls.admin, user_perm='management.change_testbuild')

        cls.staff = UserFactory()
        cls.staff_request = make_http_request(user=cls.staff)

        cls.product = ProductFactory()
        cls.another_product = ProductFactory()

        cls.build_1 = TestBuildFactory(product=cls.product)
        cls.build_2 = TestBuildFactory(product=cls.product)
        cls.build_3 = TestBuildFactory(product=cls.product)

    @unittest.skip('TODO: fix update to make this test pass.')
    def test_build_update_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.update, self.admin_request, arg, {})
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.update,
                                         self.admin_request, self.build_1.pk, {})

    def test_build_update_with_no_perms(self):
        self.assertRaisesXmlrpcFault(FORBIDDEN, build.update,
                                     self.staff_request, self.build_1.pk, {})

    def test_build_update_with_multi_id(self):
        builds = (self.build_1.pk, self.build_2.pk, self.build_3.pk)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, build.update, self.admin_request, builds, {})

    @unittest.skip('TODO: fix update to make this test pass.')
    def test_build_update_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.update, self.admin_request, arg, {})

    def test_build_update_with_non_exist_build(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.update, self.admin_request, 999, {})

    def test_build_update_with_non_exist_product_id(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.update,
                                     self.admin_request, self.build_1.pk, {"product": 9999})

    def test_build_update_with_non_exist_product_name(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.update,
                                     self.admin_request, self.build_1.pk,
                                     {"product": "AAAAAAAAAAAAAA"})

    def test_build_update(self):
        b = build.update(self.admin_request, self.build_3.pk, {
            "product": self.another_product.pk,
            "name": "Update",
            "description": "Update from unittest."
        })
        self.assertIsNotNone(b)
        self.assertEqual(b['product_id'], self.another_product.pk)
        self.assertEqual(b['name'], 'Update')
        self.assertEqual(b['description'], 'Update from unittest.')


class TestBuildGet(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.build = TestBuildFactory(description='for testing', product=cls.product)

    @unittest.skip('TODO: fix get to make this test pass.')
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.get, None, arg)

    @unittest.skip('TODO: fix get to make this test pass.')
    def test_build_get_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.get, None, arg)

    def test_build_get_with_non_exist_id(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.get, None, 9999)

    def test_build_get_with_id(self):
        b = build.get(None, self.build.pk)
        self.assertIsNotNone(b)
        self.assertEqual(b['build_id'], self.build.pk)
        self.assertEqual(b['name'], self.build.name)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertEqual(b['description'], 'for testing')
        self.assertTrue(b['is_active'])


class TestBuildGetCaseRuns(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory(name='Nitrate')
        cls.build = TestBuildFactory(product=cls.product)
        cls.user = UserFactory()
        cls.case_run_1 = TestCaseRunFactory(assignee=cls.user, build=cls.build)
        cls.case_run_2 = TestCaseRunFactory(assignee=cls.user, build=cls.build)

    @unittest.skip('TODO: fix get_caseruns to make this test pass.')
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.get_caseruns, None, arg)

    @unittest.skip('TODO: fix get_caseruns to make this test pass.')
    def test_build_get_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.get_caseruns, None, arg)

    def test_build_get_with_non_exist_id(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.get_caseruns, None, 9999)

    def test_build_get_with_id(self):
        b = build.get_caseruns(None, self.build.pk)
        self.assertIsNotNone(b)
        self.assertEqual(2, len(b))
        self.assertEqual(b[0]['case'], self.case_run_1.case.summary)


class TestBuildGetRuns(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.version = VersionFactory(value='0.1', product=cls.product)
        cls.build = TestBuildFactory(product=cls.product)
        cls.user = UserFactory()
        cls.test_run = TestRunFactory(manager=cls.user, default_tester=None,
                                      build=cls.build)

    @unittest.skip('TODO: fix get_runs to make this test pass.')
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.get_runs, None, arg)

    @unittest.skip('TODO: fix get_runs to make this test pass.')
    def test_build_get_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.get_runs, None, arg)

    def test_build_get_with_non_exist_id(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.get_runs, None, 9999)

    def test_build_get_with_id(self):
        b = build.get_runs(None, self.build.pk)
        self.assertIsNotNone(b)
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0]['summary'], self.test_run.summary)


@unittest.skip('Ignored. API is deprecated.')
class TestBuildLookupID(TestCase):
    """DEPRECATED API"""


@unittest.skip('Ignored. API is deprecated.')
class TestBuildLookupName(TestCase):
    """DEPRECATED API"""


class TestBuildCheck(XmlrpcAPIBaseTest):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.build = TestBuildFactory(description='testing ...', product=cls.product)

    @unittest.skip('TODO: fix check_build to make this test pass.')
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.check_build, None, arg, self.product.pk)
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.check_build, None, "B5", arg)

    def test_build_get_with_non_exist_build_name(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.check_build,
                                     None, "AAAAAAAAAAAAAA", self.product.pk)

    def test_build_get_with_non_exist_product_id(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.check_build, None, "B5", 9999999)

    def test_build_get_with_non_exist_product_name(self):
        self.assertRaisesXmlrpcFault(NOT_FOUND, build.check_build, None, "B5", "AAAAAAAAAAAAAAAA")

    @unittest.skip('TODO: fix check_build to make this test pass.')
    def test_build_get_with_empty(self):
        self.assertRaisesXmlrpcFault(BAD_REQUEST, build.check_build, None, "", self.product.pk)
        self.assertRaisesXmlrpcFault(BAD_REQUEST, build.check_build,
                                     None, "         ", self.product.pk)

    @unittest.skip('TODO: fix check_build to make this test pass.')
    def test_build_get_with_illegal_args(self):
        bad_args = (self, 0.7, False, True, 1, -1, 0, (1,), dict(a=1))
        for arg in bad_args:
            self.assertRaisesXmlrpcFault(BAD_REQUEST, build.check_build, None, arg, self.product.pk)

    def test_build_get(self):
        b = build.check_build(None, self.build.name, self.product.pk)
        self.assertIsNotNone(b)
        self.assertEqual(b['build_id'], self.build.pk)
        self.assertEqual(b['name'], self.build.name)
        self.assertEqual(b['product_id'], self.product.pk)
        self.assertEqual(b['description'], 'testing ...')
        self.assertEqual(b['is_active'], True)
