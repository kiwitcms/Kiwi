# -*- coding: utf-8 -*-

from tcms.tests.factories import TestPlanTypeFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestPlanTypeMethods(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestPlanTypeMethods, self)._fixture_setup()

        self.plan_type = TestPlanTypeFactory(name='xmlrpc plan type', description='')

    def test_filter(self):
        result = self.rpc_client.PlanType.filter({'name': self.plan_type.name})[0]
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])
