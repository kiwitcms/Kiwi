# -*- coding: utf-8 -*-

import json
import unittest
import http.client

from django import test
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse

from tcms.core.responses import (HttpJSONResponse,
                                 HttpJSONResponseBadRequest,
                                 HttpJSONResponseServerError)

from tcms.tests import user_should_have_perm
from tcms.tests.factories import UserFactory
from tcms.tests.factories import TestCaseRunFactory


class TestAddView(test.TestCase):
    """
        Tests the adding of link references to test case runs
    """
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('linkref-add')
        cls.testcaserun = TestCaseRunFactory()

        cls.tester = UserFactory()
        cls.tester.set_password('password')
        cls.tester.save()
        user_should_have_perm(cls.tester, 'testruns.change_testcaserun')

        cls.tester_without_perms = UserFactory()
        cls.tester_without_perms.set_password('password')
        cls.tester_without_perms.save()

    def test_without_proper_permissions(self):
        self.client.login(username=self.tester_without_perms.username, password='password')
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target_id': self.testcaserun.pk,
        })
        self.assertRedirects(response, reverse('tcms-login')+'?next=/linkref/add/')

    def test_client_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target_id': self.testcaserun.pk,
        })
        self.assertRedirects(response, reverse('tcms-login')+'?next=/linkref/add/')

    def test_with_valid_url(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target_id': self.testcaserun.pk,
        })
        self.assertEqual(http.client.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')
        self.assertEqual(result['data']['name'], 'Just a reference to a log file online')
        self.assertEqual(result['data']['url'], 'http://example.com')

    def test_with_invalid_url(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.post(self.url, {
            'name': 'Log reference with invalid URL',
            'url': 'example dot com',
            'target_id': self.testcaserun.pk,
        })
        self.assertEqual(http.client.BAD_REQUEST, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(result['rc'], 1)
        self.assertIn('Enter a valid URL', result['response'])

    def test_with_name_longer_than_64_chars(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.post(self.url, {
            'name': "Open source test case management system, with a lot of great features,"
                    "such as bug tracker integration, fast search, powerful access control"
                    "and external API.",
            'url': 'http://example.com',
            'target_id': self.testcaserun.pk,
        })
        self.assertEqual(http.client.BAD_REQUEST, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(result['rc'], 1)
        self.assertIn('Ensure this value has at most 64 characters', result['response'])


class TestCustomResponses(unittest.TestCase):
    def test_HttpJSONResponse(self):
        resp = HttpJSONResponse(content='{}')

        self.assertTrue(isinstance(resp, HttpResponse))
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.status_code, 200)

    def test_HttpJSONResponseBadRequest(self):
        resp = HttpJSONResponseBadRequest(content='{}')

        self.assertTrue(isinstance(resp, HttpResponse))
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.status_code, 400)

    def test_HttpJSONResponseServerError(self):
        resp = HttpJSONResponseServerError(content='{}')

        self.assertTrue(isinstance(resp, HttpResponse))
        self.assertEqual(resp['content-type'], 'application/json')
        self.assertEqual(resp.status_code, 500)
