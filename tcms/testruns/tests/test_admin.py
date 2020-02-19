# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
from django.urls import reverse
from tcms.tests import LoggedInTestCase
from tcms.utils.permissions import initiate_user_with_default_setups
from tcms.tests.factories import TestRunFactory


class TestTestRunAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_run = TestRunFactory()

    def test_regular_user_can_not_add_testrun(self):
        response = self.client.get(reverse('admin:testruns_testrun_add'))
        self.assertRedirects(response, reverse('admin:testruns_testrun_changelist'))

    def test_regular_user_can_not_change_testrun(self):
        response = self.client.get(reverse('admin:testruns_testrun_change',
                                           args=[self.test_run.pk]))
        self.assertRedirects(response, reverse('testruns-get', args=[self.test_run.pk]))
