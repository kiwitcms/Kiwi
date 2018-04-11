# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from http import HTTPStatus

from django.urls import reverse
from django.conf import settings

from tcms.tests import BasePlanCase


class TestAdminView(BasePlanCase):
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
        self.assertContains(response, 'Versions')

        # for tcms.testcases
        self.assertContains(response, 'Bug trackers')
        self.assertContains(response, 'Test case categories')

        self.assertNotContains(response, 'Test case status')
        self.assertNotContains(response, 'Test case texts')
        self.assertNotContains(response, 'Test cases')

        # for tcms.testplans
        self.assertContains(response, 'Plan types')

        self.assertNotContains(response, 'Test plans')

        # for tcms.testruns
        self.assertNotContains(response, 'Testruns')
        self.assertNotContains(response, 'Test case run statuss')
        self.assertNotContains(response, 'Test case run statuses')
        self.assertNotContains(response, 'Test runs')

        # for tcms.xmlrpc
        self.assertContains(response, 'Xml rpc logs')

        # for django_comments
        self.assertNotContains(response, 'Django_Comments')
        self.assertNotContains(response, 'Comments')

        # for django.contrib.sites
        self.assertContains(response, 'Sites')

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
