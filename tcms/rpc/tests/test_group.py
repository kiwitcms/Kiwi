# Copyright (c) 2025 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html
#
# pylint: disable=attribute-defined-outside-init

from django.contrib.auth.models import Group

from tcms.rpc.tests.utils import APIPermissionsTestCase
from tcms.tests import remove_perm_from_user, user_should_have_perm
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
        result = self.rpc_client.Group.permissions(Group.objects.get(name="Tester").pk)
        self.assertGreater(len(result), 0)

        self.assertIn("attachments.view_attachment", result)
        self.assertIn("management.add_product", result)
        self.assertIn("testcases.change_testcase", result)
        self.assertIn("testplans.delete_testplan", result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.permissions"'
        ):
            self.rpc_client.Group.permissions(Group.objects.get(name="Tester").pk)


class TestGroupPermissionsWithNonExistentGroup(TestGroupPermissions):
    def verify_api_with_permission(self):
        with self.assertRaisesRegex(XmlRPCFault, "Group matching query does not exist"):
            self.rpc_client.Group.permissions(99999)


class TestGroupUsersOnlyWithViewGroupPermission(APIPermissionsTestCase):
    permission_label = "auth.view_group"

    def verify_api_with_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.users"'
        ):
            self.rpc_client.Group.users(1)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.users"'
        ):
            self.rpc_client.Group.users(1)


class TestGroupUsersOnlyWithViewUserPermission(APIPermissionsTestCase):
    permission_label = "auth.view_user"

    def verify_api_with_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.users"'
        ):
            self.rpc_client.Group.users(1)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.users"'
        ):
            self.rpc_client.Group.users(1)


class TestGroupUsersWithBothPermissions(APIPermissionsTestCase):
    permission_label = "auth.view_group"
    permission_label_2 = "auth.view_user"

    def no_permissions_but(self, tested_permission):
        super().no_permissions_but(tested_permission)
        user_should_have_perm(self.tester, self.permission_label_2)

    def all_permissions_except(self, tested_permission):
        super().all_permissions_except(tested_permission)
        remove_perm_from_user(self.tester, self.permission_label_2)

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        # initialize permissions for default groups
        initiate_user_with_default_setups(UserFactory())

    def verify_api_with_permission(self):
        result = self.rpc_client.Group.users(Group.objects.get(name="Tester").pk)
        self.assertGreater(len(result), 0)

        for record in result:
            self.assertIsNotNone(record["id"])
            self.assertIsNotNone(record["username"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Group.users"'
        ):
            self.rpc_client.Group.users(1)


class TestGroupUsersWithNonExistentGroup(TestGroupUsersWithBothPermissions):
    def verify_api_with_permission(self):
        with self.assertRaisesRegex(XmlRPCFault, "Group matching query does not exist"):
            self.rpc_client.Group.users(99999)
