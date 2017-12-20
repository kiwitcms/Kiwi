# -*- coding: utf-8 -*-

from xmlrpc.client import Fault as XmlRPCFault

from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCasePlanFactory
from tcms.tests.factories import TestPlanFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestCasePlanGet(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(TestCasePlanGet, self)._fixture_setup()

        self.case = TestCaseFactory(summary='test caseplan')
        self.plan = TestPlanFactory(name='test xmlrpc')
        self.case_plan = TestCasePlanFactory(case=self.case, plan=self.plan)

    def test_get(self):
        tcp = self.rpc_client.TestCasePlan.get(self.case.pk, self.plan.pk)
        self.assertEqual(tcp['plan_id'], self.plan.pk)
        self.assertEqual(tcp['plan'], self.plan.name)
        self.assertEqual(tcp['case_id'], self.case.pk)
        self.assertEqual(tcp['case'], self.case.summary)

    def test_get_with_bad_args(self):
        bad_args = (None, [], (), {}, "A", "1", "")
        for arg in bad_args:
            with self.assertRaisesRegex(XmlRPCFault, ".*Parameter.*must be an integer"):
                self.rpc_client.TestCasePlan.get(arg, self.plan.pk)

            with self.assertRaisesRegex(XmlRPCFault, ".*Parameter.*must be an integer"):
                self.rpc_client.TestCasePlan.get(self.case.pk, arg)

    def test_get_with_non_existing(self):
        with self.assertRaisesRegex(XmlRPCFault, "TestCasePlan matching query does not exist."):
            self.rpc_client.TestCasePlan.get(-1, self.plan.pk)

        with self.assertRaisesRegex(XmlRPCFault, "TestCasePlan matching query does not exist."):
            self.rpc_client.TestCasePlan.get(self.case.pk, -1)


class TestCasePlanUpdate(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(TestCasePlanUpdate, self)._fixture_setup()

        self.case = TestCaseFactory(summary='test caseplan')
        self.plan = TestPlanFactory(name='test xmlrpc')
        self.case_plan = TestCasePlanFactory(case=self.case, plan=self.plan)

    def test_update(self):
        tcp = self.rpc_client.TestCasePlan.update(self.case.pk, self.plan.pk, 110)
        self.assertIsNotNone(tcp)
        self.assertEqual(tcp['sortkey'], 110)

    def test_update_with_bad_args(self):
        bad_args = (None, [], (), {}, "A", "1", "")
        for arg in bad_args:
            with self.assertRaisesRegex(XmlRPCFault, ".*Parameter.*must be an integer"):
                self.rpc_client.TestCasePlan.update(arg, self.plan.pk, 200)

            with self.assertRaisesRegex(XmlRPCFault, ".*Parameter.*must be an integer"):
                self.rpc_client.TestCasePlan.update(self.case.pk, arg, 200)

    def test_update_with_non_existing(self):
        with self.assertRaisesRegex(XmlRPCFault, "TestCasePlan matching query does not exist."):
            self.rpc_client.TestCasePlan.update(-1, self.plan.pk, 300)

        with self.assertRaisesRegex(XmlRPCFault, "TestCasePlan matching query does not exist."):
            self.rpc_client.TestCasePlan.update(self.case.pk, -1, 300)

    def test_update_with_non_integer_sortkey(self):
        original_sortkey = self.case_plan.sortkey
        self.rpc_client.TestCasePlan.update(self.case.pk, self.plan.pk, "A")
        self.assertEqual(original_sortkey, self.case_plan.sortkey)
