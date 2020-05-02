# -*- coding: utf-8 -*-
# pylint: disable=wrong-import-position
import unittest

from django.conf import settings

if 'tcms.bugs.apps.AppConfig' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest('tcms.bugs is disabled')

from django.urls import reverse                                         # noqa: E402

from tcms.tests import LoggedInTestCase                                 # noqa: E402
from tcms.bugs.tests.factory import BugFactory                          # noqa: E402
from tcms.utils.permissions import initiate_user_with_default_setups    # noqa: E402


class TestBugAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_bug = BugFactory()

    def test_add_view_redirects_to_new_bug_view(self):
        response = self.client.get(reverse('admin:bugs_bug_add'))
        self.assertRedirects(response, reverse('bugs-new'))

    def test_change_view_redirects_to_get_bug_view(self):
        response = self.client.get(reverse('admin:bugs_bug_change',
                                           args=[self.test_bug.pk]))
        self.assertRedirects(response, reverse('bugs-get', args=[self.test_bug.pk]))
