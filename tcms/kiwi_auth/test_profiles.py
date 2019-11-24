# pylint: disable=invalid-name
# -*- coding: utf-8 -*-

from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from tcms.tests import create_request_user


class TestProfilesView(TestCase):
    """Test the profiles view functionality"""
    @classmethod
    def setUpClass(cls):
        super(TestProfilesView, cls).setUpClass()

        cls.tester = create_request_user('tester', 'password')
        cls.somebody_else = create_request_user('somebody-else', 'password')

    def test_user_can_view_their_own_profile(self):
        logged_in = self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        self.assertTrue(logged_in)

        url = reverse('tcms-profile', args=[self.tester.username])
        response = self.client.get(url, follow=True)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.tester.username)
        self.assertContains(response, self.tester.email)
        self.assertContains(response, 'name="_save"')

    def test_user_case_view_profile_of_another_user(self):
        logged_in = self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        self.assertTrue(logged_in)

        url = reverse('tcms-profile', args=[self.somebody_else.username])
        response = self.client.get(url, follow=True)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.somebody_else.username)
        self.assertContains(response, self.somebody_else.email)
        self.assertNotContains(response, 'name="_save"')
