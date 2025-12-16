# Copyright (c) 2025 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
# pylint: disable=attribute-defined-outside-init

from django.contrib.auth.models import Group

from tcms.rpc.tests.utils import APIPermissionsTestCase
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestGroupFilter(APIPermissionsTestCase):
    permission_label = "auth.view_group"

    def verify_api_with_permission(self):
        result = self.rpc_client.Group.filter({})
        self.assertGreater(len(result), 0)

        for group in result:
            self.assertIsNotNone(group["id"])
            self.assertIsNotNone(group["name"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.filter"'
        ):
            self.rpc_client.Group.filter({})
