# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from xmlrpc.client import ProtocolError

from tcms.rpc.tests.utils import APIPermissionsTestCase
from tcms.tests.factories import PlanTypeFactory


class TestPlanTypeFilter(APIPermissionsTestCase):
    permission_label = "testplans.view_plantype"

    def _fixture_setup(self):
        super()._fixture_setup()
        self.plan_type = PlanTypeFactory(name="xmlrpc plan type", description="")

    def verify_api_with_permission(self):
        result = self.rpc_client.PlanType.filter({"name": self.plan_type.name})[0]
        self.assertEqual(self.plan_type.name, result["name"])
        self.assertEqual(self.plan_type.description, result["description"])
        self.assertEqual(self.plan_type.pk, result["id"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.PlanType.filter({"name": self.plan_type.name})
