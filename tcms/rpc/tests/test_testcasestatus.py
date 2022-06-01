# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init

from xmlrpc.client import Fault as XmlRPCFault

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase


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
