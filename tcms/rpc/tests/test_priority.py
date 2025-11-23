# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from tcms.management.models import Priority
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestPriorityFilter(APITestCase):
    """Test Priority.filter method"""

    def test_filter_priority(self):
        priorities = self.rpc_client.Priority.filter({})

        self.assertGreater(len(priorities), 0)
        for priority in priorities:
            self.assertIsNotNone(priority["id"])
            self.assertIsNotNone(priority["value"])
            self.assertIsNotNone(priority["is_active"])


class TestPriorityFilterPermissions(APIPermissionsTestCase):
    """Test permission for Priority.filter method"""

    permission_label = "management.view_priority"

    def verify_api_with_permission(self):
        priorities = self.rpc_client.Priority.filter({})
        self.assertGreater(len(priorities), 0)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Priority.filter"'
        ):
            self.rpc_client.Priority.filter({})


class TestPriorityCreate(APIPermissionsTestCase):
    permission_label = "management.add_priority"

    def verify_api_with_permission(self):
        result = self.rpc_client.Priority.create(
            {
                "value": "P99",
                "is_active": True,
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["value"], "P99")
        self.assertEqual(result["is_active"], True)

        # verify the object from the DB
        priority = Priority.objects.get(pk=result["id"])
        self.assertEqual(priority.value, result["value"])
        self.assertEqual(priority.is_active, result["is_active"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Priority.create"'
        ):
            self.rpc_client.Priority.create(
                {
                    "value": "P1000",
                    "is_active": False,
                }
            )
