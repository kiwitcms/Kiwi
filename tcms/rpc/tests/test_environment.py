# -*- coding: utf-8 -*-
from xmlrpc.client import ProtocolError

from tcms.rpc.tests.utils import APIPermissionsTestCase


class TestFilterPermission(APIPermissionsTestCase):
    permission_label = "testruns.view_environment"

    def verify_api_with_permission(self):
        result = self.rpc_client.Environment.filter()
        self.assertTrue(isinstance(result, list))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.Environment.filter(None)
