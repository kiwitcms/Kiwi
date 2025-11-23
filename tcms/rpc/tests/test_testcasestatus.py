# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init


from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testcases.models import TestCaseStatus
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestCaseStatusFilter(APITestCase):
    """Test TestCaseStatus.filter method"""

    def test_filter_case_status(self):
        case_statuses = self.rpc_client.TestCaseStatus.filter({})

        self.assertGreater(len(case_statuses), 0)
        for case_status in case_statuses:
            self.assertIsNotNone(case_status["id"])
            self.assertIsNotNone(case_status["name"])
            self.assertIsNotNone(case_status["description"])
            self.assertIsNotNone(case_status["is_confirmed"])


class TestCaseStatusFilterPermissions(APIPermissionsTestCase):
    """Test permission for TestCaseStatus.filter method"""

    permission_label = "testcases.view_testcasestatus"

    def verify_api_with_permission(self):
        case_status = self.rpc_client.TestCaseStatus.filter({})
        self.assertGreater(len(case_status), 0)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCaseStatus.filter"'
        ):
            self.rpc_client.TestCaseStatus.filter({})


class TestCaseStatusCreate(APIPermissionsTestCase):
    permission_label = "testcases.add_testcasestatus"

    def verify_api_with_permission(self):
        result = self.rpc_client.TestCaseStatus.create(
            {
                "name": "NEEDS MORE DATA",
                "description": "test case needs more information",
                "is_confirmed": False,
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], "NEEDS MORE DATA")

        # verify the object from the DB
        status = TestCaseStatus.objects.get(pk=result["id"])
        self.assertEqual(status.name, result["name"])
        self.assertEqual(status.description, result["description"])
        self.assertEqual(status.is_confirmed, result["is_confirmed"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCaseStatus.create"'
        ):
            self.rpc_client.TestCaseStatus.create(
                {
                    "name": "ALL GOOD",
                    "description": "",
                    "is_confirmed": True,
                }
            )
