# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used


from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from tcms.rpc.api.user import _get_user_dict
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.tests import remove_perm_from_user, user_should_have_perm
from tcms.tests.factories import GroupFactory, UserFactory
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestUserSerializer(TestCase):
    """Test User._get_user_dict"""

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def test_ensure_password_not_returned(self):
        data = _get_user_dict(self.user)
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["email"], self.user.email)
        self.assertNotIn("password", data)


class TestUserFilter(APITestCase):
    """Test User.filter"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        user_should_have_perm(cls.api_user, "auth.view_user")

        cls.group_tester = GroupFactory()
        cls.group_reviewer = GroupFactory()

        cls.user1 = UserFactory(
            username="user 1",
            email="user1@exmaple.com",
            is_active=True,
            groups=[cls.group_tester],
        )
        cls.user2 = UserFactory(
            username="user 2",
            email="user2@example.com",
            is_active=False,
            groups=[cls.group_reviewer],
        )
        cls.user3 = UserFactory(
            username="user 3",
            email="user3@example.com",
            is_active=True,
            groups=[cls.group_reviewer],
        )

    def test_normal_search(self):
        users = self.rpc_client.User.filter({"email": "user2@example.com"})
        self.assertEqual(len(users), 1)
        user = users[0]
        self.assertEqual(user["id"], self.user2.pk)
        self.assertEqual(user["username"], self.user2.username)

        users = self.rpc_client.User.filter(
            {"pk__in": [self.user1.pk, self.user2.pk, self.user3.pk], "is_active": True}
        )
        self.assertEqual(len(users), 2)

    def test_search_by_groups(self):
        users = self.rpc_client.User.filter({"groups__name": self.group_reviewer.name})
        self.assertEqual(len(users), 2)

    def test_get_me(self):
        # if executed without parameters returns the current user
        data = self.rpc_client.User.filter()[0]

        self.assertEqual(data["username"], self.api_user.username)
        self.assertEqual(data["id"], self.api_user.pk)
        self.assertEqual(data["first_name"], self.api_user.first_name)
        self.assertEqual(data["last_name"], self.api_user.last_name)
        self.assertEqual(data["email"], self.api_user.email)

    def test_without_permission_should_raise(self):
        remove_perm_from_user(self.api_user, "auth.view_user")

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "User.filter"'
        ):
            self.rpc_client.User.filter({})


class TestUserJoin(APITestCase):
    """Test User.join_group"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        # needs auth.change_user
        cls.api_user.is_superuser = True
        cls.api_user.save()

        cls.user = UserFactory(username="test_username", email="username@example.com")
        cls.group = GroupFactory(name="test_group")

    def test_join_normally(self):
        self.rpc_client.User.join_group(self.user.username, self.group.name)

        self.user.refresh_from_db()
        user_added_to_group = self.user.groups.filter(name=self.group.name).exists()
        self.assertTrue(user_added_to_group, "User should be added to group.")

    def test_join_nonexistent_user(self):
        with self.assertRaisesRegex(XmlRPCFault, "User matching query does not exist"):
            self.rpc_client.User.join_group("nonexistent user", self.group.name)

    def test_join_nonexistent_group(self):
        with self.assertRaisesRegex(XmlRPCFault, "Group matching query does not exist"):
            self.rpc_client.User.join_group(
                self.user.username, "nonexistent group name"
            )


class TestUserUpdate(APITestCase):
    """Test User.update"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.another_user = UserFactory()
        cls.another_user.set_password("another-password")
        cls.another_user.save()

        cls.user_new_attrs = {
            "first_name": "new first name",
            "last_name": "new last name",
            "email": "new email",
        }

    def setUp(self):
        super().setUp()
        # clear permissions b/c we set them inside individual tests
        self.api_user.user_permissions.all().delete()

    def tearDown(self):
        super().tearDown()
        self.api_user.set_password("api-testing")
        self.api_user.save()

    def test_update_myself(self):
        data = self.rpc_client.User.update(self.api_user.pk, self.user_new_attrs)
        self.assertEqual(data["first_name"], self.user_new_attrs["first_name"])
        self.assertEqual(data["last_name"], self.user_new_attrs["last_name"])
        self.assertEqual(data["email"], self.user_new_attrs["email"])

    def test_update_myself_without_passing_id(self):
        data = self.rpc_client.User.update(None, self.user_new_attrs)
        self.assertEqual(data["first_name"], self.user_new_attrs["first_name"])
        self.assertEqual(data["last_name"], self.user_new_attrs["last_name"])
        self.assertEqual(data["email"], self.user_new_attrs["email"])

    def test_update_other_missing_permission(self):
        new_values = {"some_attr": "xxx"}
        with self.assertRaisesRegex(XmlRPCFault, "Permission denied"):
            self.rpc_client.User.update(self.another_user.pk, new_values)

    def test_update_other_with_proper_permission(self):
        user_should_have_perm(self.api_user, "auth.change_user")

        data = self.rpc_client.User.update(self.another_user.pk, self.user_new_attrs)
        self.another_user.refresh_from_db()
        self.assertEqual(data["first_name"], self.another_user.first_name)
        self.assertEqual(data["last_name"], self.another_user.last_name)
        self.assertEqual(data["email"], self.another_user.email)

    def test_update_own_password(self):
        user_new_attrs = self.user_new_attrs.copy()
        new_password = "new password"  # nosec:B105:hardcoded_password_string
        user_new_attrs["password"] = (  # nosec:B105:hardcoded_password_string
            new_password
        )

        with self.assertRaisesRegex(XmlRPCFault, "Old password is required"):
            self.rpc_client.User.update(self.api_user.pk, user_new_attrs)

        user_new_attrs["old_password"] = "invalid old password"  # nosec:B105
        with self.assertRaisesRegex(XmlRPCFault, "Password is incorrect"):
            self.rpc_client.User.update(self.api_user.pk, user_new_attrs)

        user_new_attrs["old_password"] = (  # nosec:B105:hardcoded_password_string
            "api-testing"
        )
        data = self.rpc_client.User.update(self.api_user.pk, user_new_attrs)
        self.assertNotIn("password", data)
        self.assertEqual(data["first_name"], user_new_attrs["first_name"])
        self.assertEqual(data["last_name"], user_new_attrs["last_name"])
        self.assertEqual(data["email"], user_new_attrs["email"])

        self.api_user.refresh_from_db()
        self.assertTrue(self.api_user.check_password(new_password))

    def test_update_another_user_password(self):
        user_should_have_perm(self.api_user, "auth.change_user")

        user_new_attrs = self.user_new_attrs.copy()
        user_new_attrs["password"] = (  # nosec:B105:hardcoded_password_string
            "new password"
        )

        with self.assertRaisesRegex(
            XmlRPCFault, "Password updates for other users are not allowed via RPC!"
        ):
            self.rpc_client.User.update(self.another_user.pk, user_new_attrs)


class TestUserDeactivatePermissions(APIPermissionsTestCase):
    permission_label = "auth.change_user"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.group_tester = GroupFactory()
        cls.group_reviewer = GroupFactory()

        cls.user1 = UserFactory(
            username="user-1",
            email="user1@kiwitcms.org",
            is_active=True,
            groups=[cls.group_tester],
        )
        cls.user2 = UserFactory(
            username="user-2",
            email="user2@deactivate-me.com",
            is_active=True,
            groups=[cls.group_reviewer],
        )
        user_should_have_perm(cls.user2, "management.view_product")
        user_should_have_perm(cls.user2, "management.change_product")

        cls.user3 = UserFactory(
            username="user-3",
            email="user3@deactivate-me.com",
            is_active=True,
            groups=[cls.group_reviewer],
        )
        user_should_have_perm(cls.user2, "management.view_product")
        user_should_have_perm(cls.user2, "management.change_product")
        user_should_have_perm(cls.user3, "management.view_version")
        user_should_have_perm(cls.user3, "management.change_version")

    def verify_api_with_permission(self):
        initial_group_count = Group.objects.count()
        initial_perm_count = Permission.objects.count()

        for user in (self.user2, self.user3):
            self.assertGreater(user.user_permissions.count(), 0)

        result = self.rpc_client.User.deactivate(
            {"email__endswith": "@deactivate-me.com"}
        )

        # verify the serialized result
        self.assertEqual(len(result), 2)
        for data in result:
            self.assertIn("id", data)
            self.assertIn(data["username"], ["user-2", "user-3"])
            self.assertFalse(data["is_active"])
            self.assertFalse(data["is_staff"])
            self.assertFalse(data["is_superuser"])
            self.assertNotIn("password", data)

        for user in (self.user2, self.user3):
            user.refresh_from_db()
            self.assertFalse(user.is_active)
            self.assertQuerySetEqual(user.groups.all(), [])
            self.assertQuerySetEqual(user.user_permissions.all(), [])

        current_group_count = Group.objects.count()
        self.assertEqual(initial_group_count, current_group_count)

        current_perm_count = Permission.objects.count()
        self.assertEqual(initial_perm_count, current_perm_count)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "User.deactivate"'
        ):
            self.rpc_client.User.deactivate({"pk": self.user1.pk})


class TestApiAccessForDeactivatedUser(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        user_should_have_perm(cls.api_user, "auth.view_user")

        cls.group_tester = GroupFactory()

        cls.user1 = UserFactory(
            username="user 1",
            email="user1@exmaple.com",
            is_active=True,
            groups=[cls.group_tester],
        )

    def test_method_call_from_deactivated_user_account_will_raise_exception(self):
        self.api_user.is_active = False
        self.api_user.save()

        with self.assertRaisesRegex(
            XmlRPCFault, "Internal error: Wrong username or password"
        ):
            self.rpc_client.User.filter({})
