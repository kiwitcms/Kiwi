# -*- coding: utf-8 -*-

from http import HTTPStatus
from django.test import TestCase
from django.urls import reverse

from tcms.profiles.forms import BookmarkForm
from tcms.tests import create_request_user
from tcms.tests.factories import UserProfileFactory


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
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.tester.username)
        self.assertContains(response, self.tester.email)

    def test_user_case_view_profile_of_another_user(self):
        logged_in = self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        self.assertTrue(logged_in)

        url = reverse('tcms-profile', args=[self.somebody_else.username])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.somebody_else.username)
        self.assertContains(response, self.somebody_else.email)


class TestOpenBookmarks(TestCase):
    """Test for opening bookmarks"""

    @classmethod
    def setUpClass(cls):
        super(TestOpenBookmarks, cls).setUpClass()

        cls.tester = create_request_user('bookmark_tester', 'password')

        bookmark_form = BookmarkForm({
            'name': 'plan page',
            'url': 'http://localhost/plan/1/',
            'user': cls.tester.pk,
            'a': 'add',
        })
        bookmark_form.is_valid()
        cls.bookmark_1 = bookmark_form.save()

        bookmark_form = BookmarkForm({
            'name': 'case page',
            'url': 'http://localhost/case/1/',
            'user': cls.tester.pk,
            'a': 'add',
        })
        bookmark_form.is_valid()
        cls.bookmark_2 = bookmark_form.save()

        bookmark_form = BookmarkForm({
            'name': 'run page',
            'url': 'http://localhost/run/1/',
            'user': cls.tester.pk,
            'a': 'add',
        })
        bookmark_form.is_valid()
        cls.bookmark_3 = bookmark_form.save()

    def test_open_bookmark_page(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        url = reverse('tcms-bookmark',
                      kwargs={'username': self.tester.username})
        response = self.client.get(url)

        checkbox_fmt = '<input name="pk" value="{}" type="checkbox" />'

        for bookmark in (self.bookmark_1, self.bookmark_2, self.bookmark_3):
            checkbox = checkbox_fmt.format(bookmark.pk)
            self.assertContains(response, checkbox, html=True)

        self.assertContains(
            response,
            '<input value="Delete" class="sprites node_delete" type="submit">',
            html=True)


class TestUserProfile(TestCase):

    def test_user_invalid_im_type_id(self):
        """
        Given a UserProfile with im_type_id smaller than 1, or bigger than 5
        When get_im() instance method is called
        Then we expect a ValueError
        """

        user_profile = UserProfileFactory(im='NOT EMPTY', im_type_id=6)

        with self.assertRaisesRegex(ValueError, 'Invalid IM type id'):
            user_profile.get_im()
