# pylint: disable=invalid-name
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from tcms.tests import LoggedInTestCase
from tcms.tests.factories import UserFactory


class TestUserAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        # Note: by default the logged-in user is self.tester

        super().setUpTestData()

        cls.admin = UserFactory()
        cls.admin.is_superuser = True
        cls.admin.set_password('admin-password')
        cls.admin.save()

    def test_non_admin_cant_see_list_of_all_users(self):
        response = self.client.get('/admin/auth/user/')
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_non_admin_can_view_single_profile_as_readonly(self):
        response = self.client.get('/admin/auth/user/%d/change/' % self.admin.pk)
        response_str = str(response.content, encoding=settings.DEFAULT_CHARSET)

        # only 1 hidden field for csrf
        self.assertEqual(response_str.count('<input'), 1)
        self.assertContains(response, '<input type="hidden" name="csrfmiddlewaretoken"')

        # 6 readonly fields: username, first_name, last_name, email, is_active, groups
        self.assertEqual(response_str.count('grp-readonly'), 6)

        # no delete button
        self.assertNotContains(response, '/admin/auth/user/%d/delete/' % self.admin.pk)

        # no save buttons
        self.assertNotContains(response, 'name="_save"')
        self.assertNotContains(response, 'name="_addanother"')
        self.assertNotContains(response, 'name="_continue"')

    def test_non_admin_cant_delete_others(self):
        response = self.client.get('/admin/auth/user/%d/delete/' % self.admin.pk)
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_non_admin_cant_change_password_for_others(self):
        response = self.client.get('/admin/auth/user/%d/password/' % self.admin.pk)
        # redirects to change password for themselves
        self.assertRedirects(response, '/admin/password_change/')

    def test_non_admin_can_delete_myself(self):
        response = self.client.get('/admin/auth/user/%d/delete/' % self.tester.pk)

        self.assertContains(response, _("Yes, I'm sure"))
        expected = "<a href=\"/admin/auth/user/%d/change/\">%s</a>" % (self.tester.pk,
                                                                       self.tester.username)
        # 2 b/c of breadcrumbs links
        self.assertContains(response, expected, count=2)

    def test_admin_can_update_other_users(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username,
            password='admin-password')
        response = self.client.post('/admin/auth/user/%d/change/' % self.tester.pk, {
            'first_name': 'Changed by admin',
            # required fields below
            'username': self.tester.username,
            'email': self.tester.email,
            'date_joined_0': '2018-09-03',
            'date_joined_1': '13:16:25',
        }, follow=True)

        self.assertEqual(HTTPStatus.OK, response.status_code)

        self.tester.refresh_from_db()
        self.assertEqual(self.tester.first_name, 'Changed by admin')

    def test_admin_can_open_the_add_users_page(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/642
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username,
            password='admin-password')
        response = self.client.get('/admin/auth/user/add/')

        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_admin_can_add_new_users(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.admin.username,
            password='admin-password')
        response = self.client.post('/admin/auth/user/add/', {
            'username': 'added-by-admin',
            'password1': 'xo-xo-xo',
            'password2': 'xo-xo-xo',
        }, follow=True)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertTrue(get_user_model().objects.filter(username='added-by-admin').exists())
