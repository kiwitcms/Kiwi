# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.tests.factories import PlanTypeFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class PlanTypeMethods(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(PlanTypeMethods, self)._fixture_setup()

        self.plan_type = PlanTypeFactory(name='xmlrpc plan type', description='')

    def test_filter(self):
        result = self.rpc_client.exec.PlanType.filter({'name': self.plan_type.name})[0]
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])
