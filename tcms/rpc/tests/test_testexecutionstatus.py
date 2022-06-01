# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase


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
