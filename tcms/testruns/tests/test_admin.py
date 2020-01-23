# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
from django.urls import reverse
from tcms.tests import LoggedInTestCase
from tcms.utils.permissions import initiate_user_with_default_setups


class TestTestRunAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def test_regular_user_can_not_add_testrun(self):
        response = self.client.get(reverse('admin:testruns_testrun_add'))
        self.assertRedirects(response, reverse('admin:testruns_testrun_changelist'))
