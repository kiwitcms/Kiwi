# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
from django.urls import reverse
from tcms.tests import LoggedInTestCase
from tcms.utils.permissions import initiate_user_with_default_setups


class TestBugAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def test_user_clicks_add_bug_button(self):
        """
        Click the add bug button on the admin-bugs page
        Assert if being redirected to the bugs-new form
        """
        response = self.client.get(reverse('admin:bugs_bug_add'))
        self.assertRedirects(response, reverse('bugs-new'))
