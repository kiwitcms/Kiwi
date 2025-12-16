# Copyright (c) 2025 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
# pylint: disable=attribute-defined-outside-init

from tcms.rpc.tests.utils import APIPermissionsTestCase
from tcms.tests.factories import UserFactory
from tcms.utils.permissions import initiate_user_with_default_setups
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


class TestGroupPermissions(APIPermissionsTestCase):
    permission_label = "auth.view_group"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        # initialize permissions for default groups
        initiate_user_with_default_setups(UserFactory())

    def verify_api_with_permission(self):
        result = self.rpc_client.Group.permissions("Tester")
        self.assertGreater(len(result), 0)

        self.assertIn("attachments.view_attachment", result)
        self.assertIn("management.add_product", result)
        self.assertIn("testcases.change_testcase", result)
        self.assertIn("testplans.delete_testplan", result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.permissions"'
        ):
            self.rpc_client.Group.permissions("Administrator")


class TestGroupPermissionsWithNonExistentGroup(TestGroupPermissions):
    def verify_api_with_permission(self):
        with self.assertRaisesRegex(XmlRPCFault, "Group matching query does not exist"):
            self.rpc_client.Group.permissions("NonExistentGroup")
