# -*- coding: utf-8 -*-

from django import test

from tcms.xmlrpc.api import testcase as XmlrpcTestCase
from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm

from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import UserFactory

__all__ = (
    'TestNotificationRemoveCC',
    'TestUnlinkPlan',
)


class TestNotificationRemoveCC(test.TestCase):
    """ Tests the XML-RPC testcase.notication_remove_cc method """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)
        perm_name = 'testcases.change_testcase'
        user_should_have_perm(cls.http_req.user, perm_name)

        cls.default_cc = 'example@MrSenko.com'
        cls.testcase = TestCaseFactory()
        cls.testcase.emailing.add_cc(cls.default_cc)

    def test_remove_existing_cc(self):
        # initially testcase has the default CC listed
        # and we issue XMLRPC request to remove the cc
        XmlrpcTestCase.notification_remove_cc(self.http_req, self.testcase.pk, [self.default_cc])

        # now verify that the CC email has been removed
        self.assertEqual(0, self.testcase.emailing.cc_list.count())


class TestUnlinkPlan(test.TestCase):
    """ Test the XML-RPC method testcase.unlink_plan() """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)
        perm_name = 'testcases.delete_testcaseplan'
        user_should_have_perm(cls.http_req.user, perm_name)

        cls.testcase_1 = TestCaseFactory()
        cls.testcase_2 = TestCaseFactory()
        cls.plan_1 = TestPlanFactory()
        cls.plan_2 = TestPlanFactory()

        cls.testcase_1.add_to_plan(cls.plan_1)

        cls.testcase_2.add_to_plan(cls.plan_1)
        cls.testcase_2.add_to_plan(cls.plan_2)

    def test_unlink_plan_from_case_with_single_plan(self):
        result = XmlrpcTestCase.unlink_plan(self.http_req, self.testcase_1.pk, self.plan_1.pk)
        self.assertEqual(0, self.testcase_1.plan.count())
        self.assertEqual([], result)

    def test_unlink_plan_from_case_with_two_plans(self):
        result = XmlrpcTestCase.unlink_plan(self.http_req, self.testcase_2.pk, self.plan_1.pk)
        self.assertEqual(1, self.testcase_2.plan.count())
        self.assertEqual(1, len(result))
        self.assertEqual(self.plan_2.pk, result[0]['plan_id'])
