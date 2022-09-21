# pylint: disable=invalid-name
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.kiwi_auth.admin import Group
from tcms.tests import LoggedInTestCase, user_should_have_perm
from tcms.tests.factories import GroupFactory, UserFactory


class TestUserAdmin(LoggedInTestCase):  # pylint: disable=too-many-public-methods
    @classmethod
    def setUpTestData(cls):
        # Note: by default the logged-in user is self.tester
        # who is not given any permissions
        super().setUpTestData()

        cls.admin = UserFactory(username="admin")
        cls.admin.is_superuser = True
        cls.admin.set_password("admin-password")
        cls.admin.save()

        # moderator is a non-superuser who is granted specific permissions
        cls.moderator = UserFactory(username="moderator")
        cls.moderator.is_superuser = False
        cls.moderator.set_password("admin-password")
        cls.moderator.save()

    def setUp(self):
        super().setUp()
        # self.tester doesn't have any permissions
        self.assertEqual(0, self.tester.user_permissions.count())

    def test_superuser_can_view_list_of_all_users(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.admin.username)
        self.assertContains(response, self.tester.username)
        self.assertContains(response, self.moderator.username)

    def test_superuser_can_view_user_profile(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )

        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/change/")
        self.assertContains(response, self.tester.username)

    def test_superuser_can_add_users(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/642
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
        response = self.client.get("/admin/auth/user/add/")
        self.assertEqual(HTTPStatus.OK, response.status_code)

        response = self.client.post(
            "/admin/auth/user/add/",
            {
                "username": "added-by-admin",
                "password1": "xo-xo-xo",
                "password2": "xo-xo-xo",
            },
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertTrue(
            get_user_model().objects.filter(username="added-by-admin").exists()
        )

    def test_superuser_can_change_other_users(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )

        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/change/")
        response_str = str(response.content, encoding=settings.DEFAULT_CHARSET)

        # 3 readonly fields
        self.assertEqual(response_str.count("grp-readonly"), 3)

        # these fields can be edited
        self.assertContains(response, "id_first_name")
        self.assertContains(response, "id_last_name")
        self.assertContains(response, "id_email")
        self.assertContains(response, "id_is_active")
        self.assertContains(response, "id_is_staff")
        self.assertContains(response, "id_is_superuser")
        self.assertContains(response, "id_groups")
        self.assertContains(response, "id_user_permissions")

        response = self.client.post(
            f"/admin/auth/user/{self.tester.pk}/change/",
            {
                "first_name": "Changed by admin",
                # required fields below
                "username": self.tester.username,
                "email": self.tester.email,
                "date_joined_0": "2018-09-03",
                "date_joined_1": "13:16:25",
            },
            follow=True,
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)

        self.tester.refresh_from_db()
        self.assertEqual(self.tester.first_name, "Changed by admin")

    def test_superuser_can_delete_itself(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
        response = self.client.get(
            reverse("admin:auth_user_delete", args=[self.admin.pk])
        )
        self.assertContains(response, _("Yes, I'm sure"))

        response = self.client.post(
            reverse("admin:auth_user_delete", args=[self.admin.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertRedirects(response, "/accounts/login/")
        self.assertFalse(get_user_model().objects.filter(pk=self.admin.pk).exists())

    def test_superuser_can_delete_other_user(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
        response = self.client.get(
            reverse("admin:auth_user_delete", args=[self.tester.pk])
        )
        self.assertContains(response, _("Yes, I'm sure"))

        response = self.client.post(
            reverse("admin:auth_user_delete", args=[self.tester.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertRedirects(response, "/admin/auth/user/")
        self.assertFalse(get_user_model().objects.filter(pk=self.tester.pk).exists())

    def test_superuser_can_change_their_password(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )

        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/password/")
        # redirects to change password for themselves
        self.assertRedirects(response, "/admin/password_change/")

    def test_superuser_cant_change_password_for_others(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )

        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/password/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_moderator_can_view_list_of_all_users(self):
        user_should_have_perm(self.moderator, "auth.view_user")

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.admin.username)
        self.assertContains(response, self.tester.username)
        self.assertContains(response, self.moderator.username)

    def test_moderator_can_view_user_profile(self):
        user_should_have_perm(self.moderator, "auth.view_user")

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )
        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/change/")
        self.assertContains(response, self.tester.username)

        # some fields are read-only
        response_str = str(response.content, encoding=settings.DEFAULT_CHARSET)

        # only 1 hidden field for csrf
        self.assertEqual(response_str.count("<input"), 1)
        self.assertContains(response, '<input type="hidden" name="csrfmiddlewaretoken"')

        # 9 readonly fields
        self.assertEqual(response_str.count("grp-readonly"), 9)

        # no delete button
        self.assertNotContains(response, f"/admin/auth/user/{self.tester.pk}/delete/")

        # no save buttons
        self.assertNotContains(response, "_save")
        self.assertNotContains(response, "_addanother")
        self.assertNotContains(response, "_continue")

    def test_moderator_can_add_users(self):
        user_should_have_perm(self.moderator, "auth.add_user")
        user_should_have_perm(self.moderator, "auth.change_user")

        # test for https://github.com/kiwitcms/Kiwi/issues/642
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )
        response = self.client.get("/admin/auth/user/add/")
        self.assertEqual(HTTPStatus.OK, response.status_code)

        # only these fields can be edited
        self.assertContains(response, "id_username")
        self.assertContains(response, "id_password1")
        self.assertContains(response, "id_password2")

        response = self.client.post(
            "/admin/auth/user/add/",
            {
                "username": "added-by-moderator",
                "password1": "xo-xo-xo",
                "password2": "xo-xo-xo",
            },
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertTrue(
            get_user_model().objects.filter(username="added-by-moderator").exists()
        )

    def test_moderator_can_change_other_users(self):
        user_should_have_perm(self.moderator, "auth.view_user")
        user_should_have_perm(self.moderator, "auth.change_user")

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )

        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/change/")
        response_str = str(response.content, encoding=settings.DEFAULT_CHARSET)

        # 2 readonly fields
        self.assertEqual(response_str.count("grp-readonly"), 2)

        # these fields can be edited
        self.assertContains(response, "id_first_name")
        self.assertContains(response, "id_last_name")
        self.assertContains(response, "id_email")
        self.assertContains(response, "id_is_active")
        self.assertContains(response, "id_is_staff")
        self.assertContains(response, "id_groups")
        self.assertContains(response, "id_user_permissions")

        response = self.client.post(
            f"/admin/auth/user/{self.tester.pk}/change/",
            {
                "first_name": "Changed by moderator",
                # required fields below
                "username": self.tester.username,
                "email": self.tester.email,
                "date_joined_0": "2018-09-03",
                "date_joined_1": "13:16:25",
            },
            follow=True,
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)

        self.tester.refresh_from_db()
        self.assertEqual(self.tester.first_name, "Changed by moderator")

    def test_moderator_can_delete_itself(self):
        user_should_have_perm(self.moderator, "auth.delete_user")

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )
        response = self.client.get(
            reverse("admin:auth_user_delete", args=[self.moderator.pk])
        )
        self.assertContains(response, _("Yes, I'm sure"))

        response = self.client.post(
            reverse("admin:auth_user_delete", args=[self.moderator.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertRedirects(response, "/accounts/login/")
        self.assertFalse(get_user_model().objects.filter(pk=self.moderator.pk).exists())

    def test_moderator_can_delete_other_user(self):
        user_should_have_perm(self.moderator, "auth.view_user")
        user_should_have_perm(self.moderator, "auth.delete_user")

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )
        response = self.client.get(
            reverse("admin:auth_user_delete", args=[self.tester.pk])
        )
        self.assertContains(response, _("Yes, I'm sure"))

        response = self.client.post(
            reverse("admin:auth_user_delete", args=[self.tester.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        # b/c our test has only view & delete perms
        self.assertRedirects(response, "/admin/")
        self.assertFalse(get_user_model().objects.filter(pk=self.tester.pk).exists())

    def test_moderator_can_change_their_password(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )

        response = self.client.get(f"/admin/auth/user/{self.moderator.pk}/password/")
        # redirects to change password for themselves
        self.assertRedirects(response, "/admin/password_change/")

    def test_moderator_cant_change_password_for_others(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.moderator.username, password="admin-password"
        )

        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/password/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_regular_user_cant_view_list_of_all_users(self):
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_regular_user_cant_view_single_profile_without_permission(self):
        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/change/")
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_regular_user_can_view_themselves(self):
        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/change/")
        response_str = str(response.content, encoding=settings.DEFAULT_CHARSET)

        # only 1 hidden field for csrf
        self.assertContains(response, '<input type="hidden" name="csrfmiddlewaretoken"')

        # 6 readonly fields
        self.assertEqual(response_str.count("grp-readonly"), 6)

        # only these fields can be edited
        self.assertContains(response, "id_first_name")
        self.assertContains(response, "id_last_name")
        self.assertContains(response, "id_email")

        # Has Delete button
        self.assertContains(response, f"/admin/auth/user/{self.tester.pk}/delete/")

        # Has Save buttons
        self.assertContains(response, "_save")
        self.assertContains(response, "_continue")
        self.assertNotContains(response, "_addanother")

    def test_regular_user_cant_add_users(self):
        response = self.client.get("/admin/auth/user/add/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

        response = self.client.post(
            "/admin/auth/user/add/",
            {
                "username": "added-by-regular-user",
                "password1": "xo-xo-xo",
                "password2": "xo-xo-xo",
            },
            follow=True,
        )
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)
        self.assertFalse(
            get_user_model().objects.filter(username="added-by-regular-user").exists()
        )

    def test_regular_user_cant_change_other_users(self):
        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/change/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

        response = self.client.post(
            f"/admin/auth/user/{self.admin.pk}/change/",
            {
                "first_name": "Changed by regular user",
                # required fields below
                "username": self.admin.username,
                "email": self.admin.email,
                "date_joined_0": "2018-09-03",
                "date_joined_1": "13:16:25",
            },
            follow=True,
        )
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

        self.admin.refresh_from_db()
        self.assertNotEqual(self.admin.first_name, "Changed by regular user")

    def test_regular_user_can_change_themselves(self):
        response = self.client.post(
            f"/admin/auth/user/{self.tester.pk}/change/",
            {
                "first_name": "Changed by myself",
                # required fields below
                "username": self.tester.username,
                "email": self.tester.email,
                "date_joined_0": "2018-09-03",
                "date_joined_1": "13:16:25",
            },
            follow=True,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)

        self.tester.refresh_from_db()
        self.assertEqual(self.tester.first_name, "Changed by myself")

    def test_regular_user_cant_delete_others(self):
        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/delete/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_regular_user_can_delete_myself(self):
        response = self.client.get(
            reverse("admin:auth_user_delete", args=[self.tester.pk])
        )
        self.assertContains(response, _("Yes, I'm sure"))

        response = self.client.post(
            reverse("admin:auth_user_delete", args=[self.tester.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertRedirects(response, "/accounts/login/")
        self.assertFalse(get_user_model().objects.filter(pk=self.tester.pk).exists())

    def test_regular_user_can_change_their_password(self):
        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/password/")
        # redirects to change password for themselves
        self.assertRedirects(response, "/admin/password_change/")

    def test_regular_user_cant_change_password_for_others(self):
        response = self.client.get(f"/admin/auth/user/{self.moderator.pk}/password/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)


class TestGroupAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.tester.is_superuser = True
        cls.tester.save()

        cls.group = GroupFactory(name="NewGroupName")
        cls.group.save()
        cls.defaultGroups = Group.objects.filter(name__in=["Administrator", "Tester"])

    def test_should_not_be_allowed_to_change_groups_with_default_names(self):
        for group in self.defaultGroups:
            response = self.client.get(
                reverse("admin:auth_group_change", args=[group.id])
            )
            self.assertNotContains(
                response,
                f'<input type="text" name="name" value="{group.name}" class="vTextField"'
                ' maxlength="150" required="" id="id_name">',
            )
            self.assertContains(
                response, f'<div class="grp-readonly">{group.name}</div>'
            )

    def test_should_not_be_allowed_to_delete_default_groups(self):
        for group in self.defaultGroups:
            response = self.client.get(
                reverse("admin:auth_group_change", args=[group.id])
            )
            _expected_url = reverse("admin:auth_group_delete", args=[self.group.id])
            _delete = _("Delete")
            self.assertNotContains(
                response,
                f'<a href="{_expected_url}" class="grp-button grp-delete-link">{_delete}</a>',
            )

    def test_should_be_allowed_to_create_new_group(self):
        response = self.client.get(reverse("admin:auth_group_add"))
        _add_group = _("Add %s") % _("group")
        self.assertContains(response, f"<h1>{_add_group}</h1>")
        self.assertContains(
            response,
            '<input type="text" name="name" class="vTextField" '
            'maxlength="150" required id="id_name">',
        )

        # check for the user widget
        self.assertContains(
            response,
            '<select name="users" id="id_users" multiple '
            'class="selectfilter" data-field-name="users" data-is-stacked="0">',
        )
        _label = _("Users")
        self.assertContains(response, f'<label for="id_users">{_label}')

    def test_should_be_able_to_delete_a_non_default_group(self):
        response = self.client.get(
            reverse("admin:auth_group_delete", args=[self.group.id]), follow=True
        )
        _are_you_sure = _("Are you sure?")
        self.assertContains(response, f"<h1>{_are_you_sure}</h1>")

    def test_should_be_able_to_edit_a_non_default_group(self):
        response = self.client.get(
            reverse("admin:auth_group_change", args=[self.group.id])
        )
        self.assertContains(
            response,
            f'<input type="text" name="name" value="{self.group.name}" class="vTextField"'
            ' maxlength="150" required id="id_name">',
        )

    def test_should_be_allowed_to_create_new_group_with_added_user(self):
        self.assertFalse(self.tester.groups.filter(name=self.group.name).exists())

        group_name = "TestGroupName"
        response = self.client.post(
            reverse("admin:auth_group_add"),
            {"name": group_name, "users": [self.tester.id]},
            follow=True,
        )

        group = self.tester.groups.get(name=group_name)

        self.assertIsNotNone(group)
        self.assertContains(response, group_name)
        group_url = reverse("admin:auth_group_change", args=[group.pk])
        self.assertContains(
            response,
            f'<a href="{group_url}">{group_name}</a>',
        )

    def test_should_be_able_to_add_user_while_editing_a_group(self):
        self.assertFalse(self.tester.groups.filter(name=self.group.name).exists())
        response = self.client.post(
            reverse("admin:auth_group_change", args=[self.group.id]),
            {"name": self.group.name, "users": [self.tester.id], "_continue": True},
            follow=True,
        )

        self.assertContains(
            response,
            f'<option value="{self.tester.pk}" selected>{self.tester.username}</option>',
        )
        self.assertTrue(self.tester.groups.filter(name=self.group.name).exists())
