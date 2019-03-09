# -*- coding: utf-8 -*-

import json
from http import HTTPStatus

from django import test
from django.urls import reverse
from django.conf import settings
from django.utils.translation import gettext_lazy as _, ngettext_lazy

from tcms.tests import user_should_have_perm
from tcms.tests.factories import UserFactory
from tcms.tests.factories import TestExecutionFactory


class TestAddView(test.TestCase):
    """
        Tests the adding of link references to test case runs
    """
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('linkref-add')
        cls.test_execution = TestExecutionFactory()

        cls.tester = UserFactory()
        cls.tester.set_password('password')
        cls.tester.save()
        user_should_have_perm(cls.tester, 'testruns.change_testexecution')

        cls.tester_without_perms = UserFactory()
        cls.tester_without_perms.set_password('password')
        cls.tester_without_perms.save()

    def test_without_proper_permissions(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester_without_perms.username,
            password='password')
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target_id': self.test_execution.pk,
        })
        self.assertRedirects(response, reverse('tcms-login')+'?next=/linkref/add/')

    def test_client_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target_id': self.test_execution.pk,
        })
        self.assertRedirects(response, reverse('tcms-login')+'?next=/linkref/add/')

    def test_with_valid_url(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target_id': self.test_execution.pk,
        })
        self.assertEqual(HTTPStatus.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')
        self.assertEqual(result['data']['name'], 'Just a reference to a log file online')
        self.assertEqual(result['data']['url'], 'http://example.com')

    def test_with_invalid_url(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.post(self.url, {
            'name': 'Log reference with invalid URL',
            'url': 'example dot com',
            'target_id': self.test_execution.pk,
        })
        self.assertEqual(HTTPStatus.BAD_REQUEST, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(result['rc'], 1)
        self.assertIn(str(_('Enter a valid URL.')), result['response'])

    def test_with_name_longer_than_64_chars(self):  # pylint: disable=invalid-name
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.post(self.url, {
            'name': "abcdefghij-abcdefghij-abcdefghij-"
                    "abcdefghij-abcdefghij-abcdefghij-",
            'url': 'http://example.com',
            'target_id': self.test_execution.pk,
        })
        self.assertEqual(HTTPStatus.BAD_REQUEST, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(result['rc'], 1)
        message = ngettext_lazy(
            'Ensure this value has at most %(limit_value)d character (it has %(show_value)d).',
            'Ensure this value has at most %(limit_value)d characters (it has %(show_value)d).',
            'limit_value') % {'limit_value': 64, 'show_value': 66}
        self.assertIn(message, result['response'])
