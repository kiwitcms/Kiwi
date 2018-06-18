# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from http import HTTPStatus

from django.urls import reverse
from django.conf import settings

from tcms.tests import BasePlanCase, BaseCaseRun
from tcms.tests.factories import UserFactory
from tcms.tests.factories import TestCaseEmailSettingsFactory


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


class TestUserDeletionViaAdminView(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.case.email_setting = TestCaseEmailSettingsFactory(case=cls.case,
                                                              notify_on_case_update=True,
                                                              auto_to_case_author=True)

        cls.tester.is_staff = True  # can access admin
        cls.tester.save()

        cls.another_user = UserFactory()

        cls.url = reverse('admin:auth_user_delete', args=[cls.tester.pk])

    def test_delete_another_user(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(reverse('admin:auth_user_delete', args=[self.another_user.pk]))

        # it is not possible to delete other user accounts
        self.assertEqual(HTTPStatus.FORBIDDEN, response.status_code)

    def test_delete_myself(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(self.url)

        # verify there's the Yes, I'm certain button
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, "Yes, I'm sure")

        response = self.client.post(self.url, {'post': 'yes'}, follow=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, "was deleted successfully")
