# -*- coding: utf-8 -*-

import json
import unittest
import http.client

from django import test
from django.forms import Field
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponse
from django.forms import ValidationError

from .forms import TargetCharField
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
            'target': 'TestCaseRun',
            'target_id': self.testcaserun.pk,
        })
        self.assertRedirects(response, reverse('tcms-login')+'?next=/linkref/add/')

    def test_client_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target': 'TestCaseRun',
            'target_id': self.testcaserun.pk,
        })
        self.assertRedirects(response, reverse('tcms-login')+'?next=/linkref/add/')

    def test_with_valid_url(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.post(self.url, {
            'name': 'Just a reference to a log file online',
            'url': 'http://example.com',
            'target': 'TestCaseRun',
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
            'target': 'TestCaseRun',
            'target_id': self.testcaserun.pk,
        })
        self.assertEqual(http.client.BAD_REQUEST, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(result['rc'], 1)
        self.assertIn('Enter a valid URL', result['response'])


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


class TestTargetCharField(unittest.TestCase):
    class PseudoClass(object):
        pass

    def setUp(self):
        test_targets = {'TestCaseRun': self.__class__.PseudoClass}
        self.field = TargetCharField(targets=test_targets)

    def test_type(self):
        self.assertTrue(isinstance(self.field, Field))

    def test_clean(self):
        url_argu_value = 'TestCaseRun'
        self.assertEqual(self.field.clean(url_argu_value),
                         self.__class__.PseudoClass)

        url_argu_value = 'TestCase'
        with self.assertRaises(ValidationError):
            self.field.clean(url_argu_value)
