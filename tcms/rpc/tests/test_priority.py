# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from xmlrpc.client import Fault as XmlRPCFault

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase


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
