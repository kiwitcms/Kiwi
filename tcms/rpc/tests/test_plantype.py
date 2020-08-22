# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import PlanTypeFactory


class PlanTypeMethods(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan_type = PlanTypeFactory(name='xmlrpc plan type', description='')

    def test_filter(self):
        result = self.rpc_client.PlanType.filter({'name': self.plan_type.name})[0]
        self.assertEqual(self.plan_type.name, result['name'])
        self.assertEqual(self.plan_type.description, result['description'])
        self.assertEqual(self.plan_type.pk, result['id'])
