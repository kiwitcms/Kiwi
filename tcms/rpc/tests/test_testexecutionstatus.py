# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used


from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testruns.models import TestExecutionStatus
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestFilter(APITestCase):
    """Test TestExecutionStatus.filter"""

    def test_filter_statuses(self):
        execution_statuses = self.rpc_client.TestExecutionStatus.filter(
            {"weight__lt": 0}
        )

        self.assertGreater(len(execution_statuses), 0)
        for execution_status in execution_statuses:
            self.assertLess(execution_status["weight"], 0)
            self.assertIsNotNone(execution_status["id"])
            self.assertIsNotNone(execution_status["name"])
            self.assertIsNotNone(execution_status["color"])
            self.assertIsNotNone(execution_status["icon"])


class TestFilterPermission(APIPermissionsTestCase):
    """Test permission for TestExecutionStatus.filter"""

    permission_label = "testruns.view_testexecutionstatus"

    def verify_api_with_permission(self):
        execution_statuses = self.rpc_client.TestExecutionStatus.filter(
            {"weight__lt": 0}
        )
        self.assertGreater(len(execution_statuses), 0)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecutionStatus.filter"',
        ):
            self.rpc_client.TestExecutionStatus.filter({"weight__lt": 0})


class TestExecutionStatusCreate(APIPermissionsTestCase):
    permission_label = "testruns.add_testexecutionstatus"

    def verify_api_with_permission(self):
        result = self.rpc_client.TestExecutionStatus.create(
            {
                "name": "EMBARGOED",
                "weight": -50,
                "icon": "fa fa-ban",
                "color": "#ff0f1f",
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], "EMBARGOED")
        self.assertEqual(result["weight"], -50)
        self.assertEqual(result["icon"], "fa fa-ban")
        self.assertEqual(result["color"], "#ff0f1f")

        # verify the object from the DB
        status = TestExecutionStatus.objects.get(pk=result["id"])
        self.assertEqual(status.name, result["name"])
        self.assertEqual(status.weight, result["weight"])
        self.assertEqual(status.icon, result["icon"])
        self.assertEqual(status.color, result["color"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecutionStatus.create"',
        ):
            self.rpc_client.TestExecutionStatus.create(
                {
                    "name": "NOT GOOD",
                    "weight": 0,
                    "icon": "fa fa-meh-o",
                    "color": "#e3dada",
                }
            )
