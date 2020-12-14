# pylint: disable=invalid-name
# -*- coding: utf-8 -*-

from http import HTTPStatus

from django.http import HttpResponseForbidden
from django.urls import reverse

from tcms.tests import LoggedInTestCase, create_request_user, user_should_have_perm


class TestProfilesView(LoggedInTestCase):
    """Test the profiles view functionality"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.somebody_else = create_request_user("somebody-else", "password")

    def test_user_can_view_their_own_profile(self):
        url = reverse("tcms-profile", args=[self.tester.username])
        response = self.client.get(url, follow=True)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.tester.username)
        self.assertContains(response, self.tester.email)
        self.assertContains(response, 'name="_save"')

    def test_user_cant_view_profile_of_another_user_without_permission(self):
        url = reverse("tcms-profile", args=[self.somebody_else.username])
        response = self.client.get(url, follow=True)
        self.assertIsInstance(response, HttpResponseForbidden)

    def test_user_can_view_profile_of_another_user_with_permission(self):
        user_should_have_perm(self.tester, "auth.view_user")

        url = reverse("tcms-profile", args=[self.somebody_else.username])
        response = self.client.get(url, follow=True)

        self.assertContains(response, self.somebody_else.username)
        self.assertContains(response, self.somebody_else.email)
        self.assertNotContains(response, 'name="_save"')

    def test_view_if_user_is_invalid(self):
        response = self.client.get(
            reverse("tcms-profile", args=["non-existing-username"])
        )
        self.assertEqual(response.status_code, 404)
