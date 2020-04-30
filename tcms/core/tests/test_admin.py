# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import html
from http import HTTPStatus

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.tests import LoggedInTestCase
from tcms.tests.factories import UserFactory


class TestAdminView(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.tester.is_staff = True  # can access admin
        cls.tester.is_superuser = True  # has all perms
        cls.tester.save()

        cls.url = reverse('admin:index')

    def test_admin_display(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(self.url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertNotContains(response, "You don't have permission to edit anything")

        # for tcms.management
        self.assertContains(response, 'Builds')
        self.assertContains(response, 'Classifications')
        self.assertContains(response, 'Components')
        self.assertContains(response, 'Priorities')
        self.assertContains(response, 'Products')
        self.assertContains(response, 'Tags')
        self.assertContains(response, 'Versions')

        if 'tcms.bugs.apps.AppConfig' in settings.INSTALLED_APPS:
            self.assertContains(response, '<a href="/admin/bugs/" class="grp-section">%s</a>' %
                                _('Bugs'), html=True)
            self.assertContains(response, '<strong>Bugs</strong>', html=True)

        # for tcms.testcases
        self.assertContains(response, 'Bug trackers')
        self.assertContains(response, 'Test case categories')

        self.assertNotContains(response, 'Test case status')
        self.assertContains(response, 'Testcases')
        self.assertContains(response, 'Test cases')

        # for tcms.testplans
        self.assertContains(response, 'Plan types')
        self.assertContains(response, 'Testplans')
        self.assertContains(response, 'Test plans')

        # for tcms.testruns
        # b/c French translation contains characters which get HTML escaped
        response_text = html.unescape(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertIn(str(_('Test execution statuses')), response_text)

        self.assertContains(response, 'Testruns')
        self.assertContains(response, 'Test runs')

        # for django_comments
        self.assertNotContains(response, 'Django_Comments')
        self.assertNotContains(response, 'Comments')

        # for django.contrib.sites
        self.assertContains(response, _('Sites'))

    def test_sites_admin_add(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(reverse('admin:sites_site_add'))
        self.assertRedirects(response, reverse('admin:sites_site_change', args=[settings.SITE_ID]))

    def test_sites_admin_delete(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(reverse('admin:sites_site_delete', args=[settings.SITE_ID]))
        self.assertRedirects(response, reverse('admin:sites_site_change', args=[settings.SITE_ID]))

    def test_users_list_shows_is_superuser_column(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(reverse('admin:auth_user_changelist'))
        self.assertContains(response, 'column-is_superuser')


class TestUserDeletionViaAdminView(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.superuser = UserFactory()
        cls.superuser.is_staff = True
        cls.superuser.is_superuser = True
        cls.superuser.set_password('password')
        cls.superuser.save()

        cls.regular_user = UserFactory()
        cls.regular_user.is_staff = True
        cls.regular_user.set_password('password')
        cls.regular_user.save()

        cls.url = reverse('admin:auth_user_delete', args=[cls.regular_user.pk])

    def test_regular_user_should_not_delete_another_user(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.regular_user.username,
            password='password')
        response = self.client.get(reverse('admin:auth_user_delete', args=[self.superuser.pk]))

        # it is not possible to delete other user accounts
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_regular_user_should_be_able_to_delete_himself(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.regular_user.username,
            password='password')
        response = self.client.get(self.url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, _("Yes, I'm sure"))

    def test_superuser_should_be_able_to_delete_any_user(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.superuser.username,
            password='password')
        response = self.client.get(self.url)

        # verify there's the Yes, I'm certain button
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, _("Yes, I'm sure"))
        response = self.client.post(self.url, {'post': 'yes'}, follow=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertNotContains(response, '<a href="/admin/auth/user/%d/change/">%s</a>' %
                               (self.regular_user.pk, self.regular_user.username), html=True)
