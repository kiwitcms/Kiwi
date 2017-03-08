# -*- coding: utf-8 -*-

from django import test

from tcms.testcases.models import TestCasePlan
from tcms.xmlrpc.api import testcase as XmlrpcTestCase
from tcms.xmlrpc.tests.utils import make_http_request
from tcms.xmlrpc.tests.utils import user_should_have_perm

from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import UserFactory


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


class TestLinkPlan(test.TestCase):
    """ Test the XML-RPC method testcase.link_plan() """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_req = make_http_request(user=cls.user)
        perm_name = 'testcases.add_testcaseplan'
        user_should_have_perm(cls.http_req.user, perm_name)

        cls.testcase_1 = TestCaseFactory()
        cls.testcase_2 = TestCaseFactory()
        cls.testcase_3 = TestCaseFactory()

        cls.plan_1 = TestPlanFactory()
        cls.plan_2 = TestPlanFactory()
        cls.plan_3 = TestPlanFactory()

        # case 1 is already linked to plan 1
        cls.testcase_1.add_to_plan(cls.plan_1)

    def test_insert_ignores_existing_mappings(self):
        plans = [self.plan_1.pk, self.plan_2.pk, self.plan_3.pk]
        cases = [self.testcase_1.pk, self.testcase_2.pk, self.testcase_3.pk]
        XmlrpcTestCase.link_plan(self.http_req, cases, plans)

        # no duplicates for plan1/case1 were created
        self.assertEqual(
            1,
            TestCasePlan.objects.filter(
                plan=self.plan_1.pk,
                case=self.testcase_1.pk
            ).count()
        )

        # verify all case/plan combinations exist
        for plan_id in plans:
            for case_id in cases:
                self.assertEqual(
                    1,
                    TestCasePlan.objects.filter(
                        plan=plan_id,
                        case=case_id
                    ).count()
                )
