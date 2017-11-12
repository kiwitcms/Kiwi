# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse

from tcms.profiles.forms import BookmarkForm


class TestOpenBookmarks(TestCase):
    """Test for opening bookmarks"""

    @classmethod
    def setUpClass(cls):
        super(TestOpenBookmarks, cls).setUpClass()

        cls.tester = User.objects.create_user(username='bookmark_tester',
                                              email='bookmark_tester@example.com',
                                              password='password')

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
        self.client.login(username=self.tester.username, password='password')

        url = reverse('user-bookmark',
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
