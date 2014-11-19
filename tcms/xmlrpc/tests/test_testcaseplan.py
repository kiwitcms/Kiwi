# -*- coding: utf-8 -*-
from xmlrpclib import Fault

from django.test import TestCase

from tcms.xmlrpc.api import testcaseplan


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


class TestCasePlanGet(TestCase):
    def test_get(self):
        try:
            tcp = testcaseplan.get(None, 1, 1)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcp)
            self.assertEqual(tcp['plan_id'], 1)
            self.assertEqual(tcp['plan'], 'StarCraft: Init')
            self.assertEqual(tcp['case_id'], 1)
            self.assertEqual(tcp['case'], 'PVZ')

    def test_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaseplan.get(None, arg, 1)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaseplan.get(None, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_no_exist_case(self):
        try:
            testcaseplan.get(None, 10000, 1)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_no_exist_plan(self):
        try:
            testcaseplan.get(None, 1, 10000)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_non_integer_case_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.get(None, arg, 1)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_non_integer_plan_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.get(None, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_negative_plan_id(self):
        try:
            testcaseplan.get(None, 1, -1)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_negative_case_id(self):
        try:
            testcaseplan.get(None, -1, 1)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCasePlanUpdate(TestCase):
    def test_update(self):
        try:
            tcp = testcaseplan.update(None, 1, 1, 110)
        except Fault:
            self.fail(AssertMessage.UNEXCEPT_ERROR)
        else:
            self.assertIsNotNone(tcp)
            self.assertEqual(tcp['plan_id'], 1)
            self.assertEqual(tcp['plan'], 'StarCraft: Init')
            self.assertEqual(tcp['case_id'], 1)
            self.assertEqual(tcp['case'], 'PVZ')
            self.assertEqual(tcp['sortkey'], 110)

    def test_update_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaseplan.update(None, arg, 1, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaseplan.update(None, 1, arg, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaseplan.update(None, 1, 1, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_no_exist_case(self):
        try:
            testcaseplan.update(None, 10000, 1, 100)
        except Fault as f:
            print f.faultString
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_no_exist_plan(self):
        try:
            testcaseplan.update(None, 1, 10000, 100)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_integer_case_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.update(None, arg, 1, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_integer_plan_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.update(None, 1, arg, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_negative_plan_id(self):
        try:
            testcaseplan.update(None, 1, -1, 100)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_negative_case_id(self):
        try:
            testcaseplan.update(None, -1, 1, 100)
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_integer_sortkey(self):
        try:
            testcaseplan.update(None, 1, 1, "A")
        except Fault as f:
            self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)
