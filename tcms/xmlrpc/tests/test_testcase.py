# -*- coding: utf-8 -*-

from tcms.testcases.models import TestCasePlan

from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseCategoryFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestNotificationRemoveCC(XmlrpcAPIBaseTest):
    """ Tests the XML-RPC testcase.notication_remove_cc method """

    def _fixture_setup(self):
        super(TestNotificationRemoveCC, self)._fixture_setup()

        self.default_cc = 'example@MrSenko.com'
        self.testcase = TestCaseFactory()
        self.testcase.emailing.add_cc(self.default_cc)

    def tearDown(self):
        super(TestNotificationRemoveCC, self).tearDown()
        self.rpc_client.Auth.logout()

    def test_remove_existing_cc(self):
        # initially testcase has the default CC listed
        # and we issue XMLRPC request to remove the cc
        self.rpc_client.TestCase.notification_remove_cc(self.testcase.pk, [self.default_cc])

        # now verify that the CC email has been removed
        self.assertEqual(0, self.testcase.emailing.cc_list.count())


class TestUnlinkPlan(XmlrpcAPIBaseTest):
    """ Test the XML-RPC method testcase.unlink_plan() """

    def _fixture_setup(self):
        super(TestUnlinkPlan, self)._fixture_setup()
        self.testcase_1 = TestCaseFactory()
        self.testcase_2 = TestCaseFactory()
        self.plan_1 = TestPlanFactory()
        self.plan_2 = TestPlanFactory()

        self.testcase_1.add_to_plan(self.plan_1)

        self.testcase_2.add_to_plan(self.plan_1)
        self.testcase_2.add_to_plan(self.plan_2)

    def test_unlink_plan_from_case_with_single_plan(self):
        result = self.rpc_client.TestCase.unlink_plan(self.testcase_1.pk, self.plan_1.pk)
        self.assertEqual(0, self.testcase_1.plan.count())
        self.assertEqual([], result)

    def test_unlink_plan_from_case_with_two_plans(self):
        result = self.rpc_client.TestCase.unlink_plan(self.testcase_2.pk, self.plan_1.pk)
        self.assertEqual(1, self.testcase_2.plan.count())
        self.assertEqual(1, len(result))
        self.assertEqual(self.plan_2.pk, result[0]['plan_id'])


class TestLinkPlan(XmlrpcAPIBaseTest):
    """ Test the XML-RPC method testcase.link_plan() """

    def _fixture_setup(self):
        super(TestLinkPlan, self)._fixture_setup()

        self.testcase_1 = TestCaseFactory()
        self.testcase_2 = TestCaseFactory()
        self.testcase_3 = TestCaseFactory()

        self.plan_1 = TestPlanFactory()
        self.plan_2 = TestPlanFactory()
        self.plan_3 = TestPlanFactory()

        # case 1 is already linked to plan 1
        self.testcase_1.add_to_plan(self.plan_1)

    def test_insert_ignores_existing_mappings(self):
        plans = [self.plan_1.pk, self.plan_2.pk, self.plan_3.pk]
        cases = [self.testcase_1.pk, self.testcase_2.pk, self.testcase_3.pk]
        self.rpc_client.TestCase.link_plan(cases, plans)

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


class TestFilterCases(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestFilterCases, self)._fixture_setup()

        self.tester = UserFactory(username='great tester')
        self.product = ProductFactory(name='StarCraft')
        self.version = VersionFactory(value='0.1', product=self.product)
        self.plan = TestPlanFactory(name='Test product.get_cases',
                                    owner=self.tester, author=self.tester,
                                    product=self.product,
                                    product_version=self.version)
        self.case_category = TestCaseCategoryFactory(product=self.product)
        self.cases_count = 10
        self.cases = [TestCaseFactory(category=self.case_category, author=self.tester,
                                      reviewer=self.tester, default_tester=None,
                                      plan=[self.plan])
                      for i in range(self.cases_count)]

    def test_filter_by_product_id(self):
        cases = self.rpc_client.TestCase.filter({'category__product': self.product.pk})
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)
