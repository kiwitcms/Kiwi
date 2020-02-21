# -*- coding: utf-8 -*-
from http import HTTPStatus

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.testcases.models import TestCase
from tcms.tests import BasePlanCase
from tcms.utils.permissions import initiate_user_with_default_setups


class TestTestCaseUpdates(BasePlanCase):
    """
        Tests for TC bulk update actions triggered via
        TP sub-menu.
    """
    def _assert_default_tester_is(self, expected_value):
        for test_case in TestCase.objects.filter(plan=self.plan):
            self.assertEqual(test_case.default_tester, expected_value)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.url = reverse('ajax.update.cases-actor')
        cls.case_pks = []
        for case in TestCase.objects.filter(plan=cls.plan):
            cls.case_pks.append(case.pk)

    def setUp(self):
        super().setUp()
        self._assert_default_tester_is(None)

    def test_update_default_tester_via_username(self):
        response = self.client.post(self.url, {
            'case[]': self.case_pks,
            'what_to_update': 'default_tester',
            'username': self.tester.username
        })

        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})
        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_via_email(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/85
        response = self.client.post(self.url, {
            'case[]': self.case_pks,
            'what_to_update': 'default_tester',
            'username': self.tester.email
        })

        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})
        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_non_existing_user(self):
        username = 'user which doesnt exist'
        response = self.client.post(self.url, {
            'case[]': self.case_pks,
            'what_to_update': 'default_tester',
            'username': username
        })

        self.assertJsonResponse(
            response,
            {'rc': 1, 'response': _('User %s not found!') % username},
            HTTPStatus.NOT_FOUND)
        self._assert_default_tester_is(None)
