# -*- coding: utf-8 -*-
import json
import http.client

from django import test
from django.urls import reverse
from django.conf import settings

from tcms.testcases.models import TestCase
from tcms.tests import BasePlanCase

from tcms.core.contrib.auth.backends import initiate_user_with_default_setups


class TestInfo(test.TestCase):

    def test_lowercase_string_is_converted_to_bool(self):
        url = "%s?info_type=builds&product_id=1&is_active=true" % reverse('ajax-info')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_empty_string_is_converted_to_bool(self):
        url = "%s?info_type=builds&product_id=1&is_active=" % reverse('ajax-info')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)


class Test_TestCaseUpdateActions(BasePlanCase):
    """
        Tests for TC bulk update actions triggered via
        TP sub-menu.
    """
    def _assert_default_tester_is(self, expected_value):
        for test_case in TestCase.objects.filter(plan=self.plan):
            self.assertEqual(test_case.default_tester, expected_value)

    @classmethod
    def setUpTestData(cls):
        super(Test_TestCaseUpdateActions, cls).setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def setUp(self):
        self.login_tester()
        self._assert_default_tester_is(None)

    def test_update_default_tester_via_username(self):
        url = reverse('ajax-update_cases_default_tester')
        response = self.client.post(url, {
            'from_plan': self.plan.pk,
            'case': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'target_field': 'default_tester',
            'new_value': self.tester.username
        })

        self.assertEqual(http.client.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')

        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_via_email(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/85
        url = reverse('ajax-update_cases_default_tester')
        response = self.client.post(url, {
            'from_plan': self.plan.pk,
            'case': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'target_field': 'default_tester',
            'new_value': self.tester.email
        })

        self.assertEqual(http.client.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')

        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_non_existing_user(self):
        url = reverse('ajax-update_cases_default_tester')
        response = self.client.post(url, {
            'from_plan': self.plan.pk,
            'case': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'target_field': 'default_tester',
            'new_value': 'user which doesnt exist'
        })

        self.assertEqual(http.client.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 1)
        self.assertEqual(result['response'], 'Default tester not found!')

        self._assert_default_tester_is(None)
