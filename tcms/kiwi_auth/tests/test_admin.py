# pylint: disable=invalid-name
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from tcms.kiwi_auth.admin import Group
from tcms.tests import LoggedInTestCase, user_should_have_perm
from tcms.tests.factories import GroupFactory, UserFactory


class TestUserAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        # Note: by default the logged-in user is self.tester

        super().setUpTestData()

        cls.admin = UserFactory()
        cls.admin.is_superuser = True
        cls.admin.set_password("admin-password")
        cls.admin.save()

    def test_non_admin_cant_see_list_of_all_users(self):
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_non_admin_cant_view_single_profile_without_permission(self):
        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/change/")
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_non_admin_can_view_single_profile_as_readonly_if_permission(self):
        user_should_have_perm(self.tester, "auth.view_user")

        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/change/")
        response_str = str(response.content, encoding=settings.DEFAULT_CHARSET)

        # only 1 hidden field for csrf
        self.assertEqual(response_str.count("<input"), 1)
        self.assertContains(response, '<input type="hidden" name="csrfmiddlewaretoken"')

        # 6 readonly fields: username, first_name, last_name, email, is_active, groups
        self.assertEqual(response_str.count("grp-readonly"), 6)

        # no delete button
        self.assertNotContains(response, f"/admin/auth/user/{self.admin.pk}/delete/")

        # no save buttons
        self.assertNotContains(response, 'name="_save"')
        self.assertNotContains(response, 'name="_addanother"')
        self.assertNotContains(response, 'name="_continue"')

    def test_non_admin_cant_delete_others(self):
        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/delete/")
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_non_admin_cant_change_password_for_others(self):
        response = self.client.get(f"/admin/auth/user/{self.admin.pk}/password/")
        # redirects to change password for themselves
        self.assertRedirects(response, "/admin/password_change/")

    def test_non_admin_can_delete_myself(self):
        response = self.client.get(f"/admin/auth/user/{self.tester.pk}/delete/")

        self.assertContains(response, _("Yes, I'm sure"))
        expected = f'<a href="/admin/auth/user/{self.tester.pk}/change/">{self.tester.username}</a>'
        # 2 b/c of breadcrumbs links
        self.assertContains(response, expected, count=2)

    def test_admin_can_update_other_users(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
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

    def test_admin_can_open_the_add_users_page(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/642
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
        response = self.client.get("/admin/auth/user/add/")

        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_admin_can_add_new_users(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
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

    def test_admin_can_delete_itself(self):
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

        self.assertRedirects(response, "/accounts/login/?next=/")

    def test_admin_can_delete_other_user(self):
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

    def test_admin_can_see_list_of_all_users(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username, password="admin-password"
        )
        response = self.client.get("/admin/auth/user/")
        self.assertEqual(HTTPStatus.OK, response.status_code)


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
        _capfirst = capfirst(_("users"))
        self.assertContains(response, f'<label for="id_users">{_capfirst}')

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
