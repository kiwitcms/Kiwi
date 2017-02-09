# -*- coding: utf-8 -*-

import unittest
from xmlrpclib import Fault

from django.test import TestCase

from tcms.xmlrpc.api import testcaseplan
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCasePlanFactory
from tcms.tests.factories import TestPlanFactory


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

    @classmethod
    def setUpClass(cls):
        super(TestCasePlanGet, cls).setUpClass()
        cls.case = TestCaseFactory(summary='test caseplan')
        cls.plan = TestPlanFactory(name='test xmlrpc')
        cls.case_plan = TestCasePlanFactory(case=cls.case, plan=cls.plan)

    def test_get(self):
        tcp = testcaseplan.get(None, self.case.pk, self.plan.pk)
        self.assertEqual(tcp['plan_id'], self.plan.pk)
        self.assertEqual(tcp['plan'], self.plan.name)
        self.assertEqual(tcp['case_id'], self.case.pk)
        self.assertEqual(tcp['case'], self.case.summary)

    @unittest.skip('TODO: fix get to make this test pass.')
    def test_get_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaseplan.get(None, arg, self.plan.pk)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaseplan.get(None, self.case.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_no_exist_case(self):
        try:
            testcaseplan.get(None, 10000, self.plan.pk)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_no_exist_plan(self):
        try:
            testcaseplan.get(None, self.case.pk, 10000)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix get to make this test pass.')
    def test_get_with_non_integer_case_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.get(None, arg, self.plan.pk)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix get to make this test pass.')
    def test_get_with_non_integer_plan_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.get(None, self.case.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_negative_plan_id(self):
        try:
            testcaseplan.get(None, self.case.pk, -1)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_get_with_negative_case_id(self):
        try:
            testcaseplan.get(None, -1, self.plan.pk)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_400)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)


class TestCasePlanUpdate(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestCasePlanUpdate, cls).setUpClass()
        cls.case = TestCaseFactory(summary='test caseplan')
        cls.plan = TestPlanFactory(name='test xmlrpc')
        cls.case_plan = TestCasePlanFactory(case=cls.case, plan=cls.plan)

    def test_update(self):
        tcp = testcaseplan.update(None, self.case.pk, self.plan.pk, 110)
        self.assertIsNotNone(tcp)
        self.assertEqual(tcp['sortkey'], 110)

    @unittest.skip('TODO: fix update to make this test pass.')
    def test_update_with_no_args(self):
        bad_args = (None, [], (), {})
        for arg in bad_args:
            try:
                testcaseplan.update(None, arg, self.plan.pk, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaseplan.update(None, self.case.pk, arg, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

            try:
                testcaseplan.update(None, self.case.pk, self.plan.pk, arg)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_no_exist_case(self):
        try:
            testcaseplan.update(None, 10000, self.plan.pk, 100)
        except Fault as f:
            print f.faultString
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_no_exist_plan(self):
        try:
            testcaseplan.update(None, self.case.pk, 10000, 100)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix update to make this test pass.')
    def test_update_with_non_integer_case_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.update(None, arg, self.plan.pk, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    @unittest.skip('TODO: fix update to make this test pass.')
    def test_update_with_non_integer_plan_id(self):
        bad_args = ("A", "1", "", True, False, self, (1,))
        for arg in bad_args:
            try:
                testcaseplan.update(None, self.case.pk, arg, 100)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_negative_plan_id(self):
        try:
            testcaseplan.update(None, self.case.pk, -1, 100)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_negative_case_id(self):
        try:
            testcaseplan.update(None, -1, self.plan.pk, 100)
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.NOT_VALIDATE_ARGS)

    def test_update_with_non_integer_sortkey(self):
        original_sortkey = self.case_plan.sortkey
        testcaseplan.update(None, self.case.pk, self.plan.pk, "A")
        self.assertEqual(original_sortkey, self.case_plan.sortkey)
