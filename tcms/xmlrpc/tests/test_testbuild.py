# -*- coding: utf-8 -*-
from xmlrpclib import Fault

from django.contrib.auth.models import User
from django.test import TestCase

from tcms.xmlrpc.api import build
from tcms.xmlrpc.tests.utils import make_http_request


class AssertMessage(object):
    NOT_VALIDATE_ARGS = "Missing validations for args."
    NOT_VALIDATE_REQUIRED_ARGS = "Missing validations for required args."
    NOT_VALIDATE_ILLEGAL_ARGS = "Missing validations for illegal args."
    NOT_VALIDATE_FOREIGN_KEY = "Missing validations for foreign key."
    NOT_VALIDATE_LENGTH = "Missing validations for length of value."
    NOT_VALIDATE_URL_FORMAT = "Missing validations for URL format."

    SHOULD_BE_400 = "Error code should be 400."
    SHOULD_BE_409 = "Error code should be 409."
    SHOULD_BE_500 = "Error code should be 500."
    SHOULD_BE_403 = "Error code should be 403."
    SHOULD_BE_401 = "Error code should be 401."
    SHOULD_BE_404 = "Error code should be 404."
    SHOULD_BE_501 = "Error code should be 501."
    SHOULD_BE_1 = "Error code should be 1."

    UNEXCEPT_ERROR = "Unexcept error occurs."
    NEED_ENCODE_UTF8 = "Need to encode with utf8."

    NOT_IMPLEMENT_FUNC = "Not implement yet."
    XMLRPC_INTERNAL_ERROR = "xmlrpc library error."
    NOT_VALIDATE_PERMS = "Missing validations for user perms."


class TestBuildCreate(TestCase):
    def setUp(self):
        super(TestBuildCreate, self).setUp()
        self.admin = User(username='create_admin',
                          email='create_admin@example.com')
        self.admin.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='management.add_testbuild'
        )

        self.staff = User(username='create_staff',
                          email='create_staff@example.com')
        self.staff.save()
        self.staff_request = make_http_request(
            user=self.staff,
        )

    def tearDown(self):
        super(TestBuildCreate, self).tearDown()
        self.admin.delete()
        self.staff.delete()

    def test_build_create_with_no_args(self):
        bad_args = (self.admin_request, [], (), {})
        for arg in bad_args:
            try:
                build.create(self.admin_request, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_create_with_no_perms(self):
        try:
            build.create(self.staff_request, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_create_with_no_required_fields(self):
        def _create(data):
            try:
                build.create(self.admin_request, data)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        values = {
            "description": "Test Build",
            "is_active": False
        }
        _create(values)

        values["name"] = "TB"
        _create(values)

        del values["name"]
        values["product"] = 4
        _create(values)

    def test_build_create_with_illegal_fields(self):
        values = {
            "product": 89,
            "name": "B7",
            "milestone": "aaaaaaaa"
        }
        try:
            build.create(self.admin_request, values)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_create_with_non_exist_product(self):
        values = {
            "product": 89,
            "name": "B7",
            "description": "Test Build",
            "is_active": False
        }
        try:
            build.create(self.admin_request, values)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        values['product'] = "AAAAAAAAAA"
        try:
            build.create(self.admin_request, values)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_create_with_chinese(self):
        values = {
            "product": 4,
            "name": "B99",
            "description": "开源中国",
            "is_active": False
        }
        try:
            b = build.create(self.admin_request, values)
        except Fault as f:
            print f.faultString
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(b)
            self.assertEqual(b['product_id'], 4)
            self.assertEqual(b['name'], "B99")
            self.assertEqual(b['description'],
                             '\xe5\xbc\x80\xe6\xba\x90\xe4\xb8\xad\xe5\x9b\xbd')
            self.assertEqual(b['is_active'], False)

    def test_build_create(self):
        values = {
            "product": 4,
            "name": "B7",
            "description": "Test Build",
            "is_active": False
        }
        try:
            b = build.create(self.admin_request, values)
        except Fault as f:
            print f.faultString
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(b)
            self.assertEqual(b['product_id'], 4)
            self.assertEqual(b['name'], "B7")
            self.assertEqual(b['description'], "Test Build")
            self.assertEqual(b['is_active'], False)


class TestBuildUpdate(TestCase):
    def setUp(self):
        super(TestBuildUpdate, self).setUp()
        self.admin = User(username='create_admin',
                          email='create_admin@example.com')
        self.admin.save()
        self.admin_request = make_http_request(
            user=self.admin,
            user_perm='management.change_testbuild'
        )

        self.staff = User(username='create_staff',
                          email='create_staff@example.com')
        self.staff.save()
        self.staff_request = make_http_request(
            user=self.staff,
        )

    def tearDown(self):
        super(TestBuildUpdate, self).tearDown()
        self.admin.delete()
        self.staff.delete()

    def test_build_update_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                build.update(self.admin_request, arg, {})
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                build.update(self.admin_request, 1, {})
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_update_with_no_perms(self):
        try:
            build.update(self.staff_request, 1, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_update_with_multi_id(self):
        try:
            build.update(self.admin_request, (1, 2, 3), {})
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_update_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            try:
                build.update(self.admin_request, arg, {})
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_update_with_non_exist_build(self):
        try:
            build.update(self.admin_request, 999, {})
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_update_with_non_exist_product_id(self):
        try:
            build.update(self.admin_request, 1, {
                "product": 9999
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_update_with_non_exist_product_name(self):
        try:
            build.update(self.admin_request, 1, {
                "product": "AAAAAAAAAAAAAA"
            })
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_update(self):
        try:
            b = build.update(self.admin_request, 3, {
                "product": 1,
                "name": "Update",
                "description": "Update from unittest."
            })
        except Fault as f:
            print f.faultString
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(b)
            self.assertEqual(b['product_id'], 1)
            self.assertEqual(b['name'], 'Update')
            self.assertEqual(b['description'], 'Update from unittest.')


class TestBuildGet(TestCase):
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                build.get(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            try:
                build.get(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_exist_id(self):
        try:
            build.get(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_id(self):
        try:
            b = build.get(None, 10)
        except Fault as f:
            print f.faultString
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(b)
            self.assertEqual(b['build_id'], 10)
            self.assertEqual(b['name'], "B1")
            self.assertEqual(b['product_id'], 4)
            self.assertEqual(b['description'], "B1")
            self.assertEqual(b['is_active'], True)


class TestBuildGetCaseRuns(TestCase):
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                build.get_caseruns(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            try:
                build.get_caseruns(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_exist_id(self):
        try:
            build.get_caseruns(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_id(self):
        try:
            b = build.get_caseruns(None, 5)
        except Fault as f:
            print f.faultString
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(b)
            self.assertEqual(len(b), 5)
            self.assertEqual(b[0]['case'], "PVZ")


class TestBuildGetRuns(TestCase):
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                build.get_runs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_integer(self):
        bad_args = (True, False, (1,), dict(a=1), -1, 0.7, "", "AA")
        for arg in bad_args:
            try:
                build.get_runs(None, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_exist_id(self):
        try:
            build.get_runs(None, 9999)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_id(self):
        try:
            b = build.get_runs(None, 5)
        except Fault as f:
            print f.faultString
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(b)
            self.assertEqual(len(b), 1)
            self.assertEqual(b[0]['summary'], "Test run for StarCraft: Init "
                                              "on Unknown environment")


class TestBuildLookupID(TestCase):
    """
    DEPRECATED API
    """
    pass


class TestBuildLookupName(TestCase):
    """
    DEPRECATED API
    """
    pass


class TestBuildCheck(TestCase):
    def test_build_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                build.check_build(None, arg, 4)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                build.check_build(None, "B5", arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_exist_build_name(self):
        try:
            build.check_build(None, "AAAAAAAAAAAAAA", 4)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_exist_product_id(self):
        try:
            build.check_build(None, "B5", 99)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_non_exist_product_name(self):
        try:
            build.check_build(None, "B5", "AAAAAAAAAAAAAAAA")
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_empty(self):
        try:
            build.check_build(None, "", 4)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

        try:
            build.check_build(None, "         ", 4)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get_with_illegal_args(self):
        bad_args = (self, 0.7, False, True, 1, -1, 0, (1,), dict(a=1))
        for arg in bad_args:
            try:
                build.check_build(None, arg, 4)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_build_get(self):
        try:
            b = build.check_build(None, "B5", 4)
        except Fault as f:
            print f.faultString
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(b)
            self.assertEqual(b['build_id'], 14)
            self.assertEqual(b['name'], "B5")
            self.assertEqual(b['product_id'], 4)
            self.assertEqual(b['description'], "B5")
            self.assertEqual(b['is_active'], True)
