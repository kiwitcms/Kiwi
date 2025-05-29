# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init


from tcms.rpc.tests.utils import APIPermissionsTestCase
from tcms.testplans.models import PlanType
from tcms.tests.factories import PlanTypeFactory
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestPlanTypeFilter(APIPermissionsTestCase):
    permission_label = "testplans.view_plantype"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        cls.plan_type = PlanTypeFactory(name="xmlrpc plan type", description="")

    def verify_api_with_permission(self):
        result = self.rpc_client.PlanType.filter({"name": self.plan_type.name})[0]
        self.assertEqual(self.plan_type.name, result["name"])
        self.assertEqual(self.plan_type.description, result["description"])
        self.assertEqual(self.plan_type.pk, result["id"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "PlanType.filter"'
        ):
            self.rpc_client.PlanType.filter({"name": self.plan_type.name})


class TestPlanTypeCreate(APIPermissionsTestCase):
    permission_label = "testplans.add_plantype"

    def verify_api_with_permission(self):
        result = self.rpc_client.PlanType.create({"name": "API-TP"})
        self.assertEqual(result["name"], "API-TP")
        self.assertIn("description", result)
        self.assertIn("id", result)

        obj_from_db = PlanType.objects.get(pk=result["id"])
        self.assertEqual(result["name"], obj_from_db.name)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "PlanType.create"'
        ):
            self.rpc_client.PlanType.create({"name": "API-TP"})
