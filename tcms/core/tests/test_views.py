# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors
from http import HTTPStatus

from django import test
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.tests import BaseCaseRun
from tcms.tests.factories import (TestExecutionFactory, TestPlanFactory,
                                  TestRunFactory, UserFactory)


class TestNavigation(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestNavigation, cls).setUpTestData()
        cls.user = UserFactory(email='user+1@example.com')
        cls.user.set_password('testing')
        cls.user.save()

    def test_navigation_displays_currently_for_logged_user(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.user.username,
            password='testing')
        response = self.client.get(reverse('iframe-navigation'))

        self.assertContains(response, self.user.username)
        self.assertContains(response, _('My profile'))
        self._common_navigation_assertions(response)

    def test_navigation_displays_currently_for_guest_user(self):
        response = self.client.get(reverse('iframe-navigation'))
        self.assertContains(response, _('Welcome Guest'))
        self._common_navigation_assertions(response)

    def _common_navigation_assertions(self, response):
        self.assertContains(response, _('DASHBOARD'))
        self.assertContains(response, _('TESTING'))
        self.assertContains(response, _('SEARCH'))
        self.assertContains(response, _('TELEMETRY'))
        self.assertContains(response, _('ADMIN'))


class TestDashboard(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # used to reproduce Sentry #KIWI-TCMS-38 where rendering fails
        # with that particular value
        cls.chinese_tp = TestPlanFactory(name="缺货反馈测试需求",
                                         author=cls.tester)

    def test_when_not_logged_in_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('core-views-index'))
        self.assertRedirects(
            response,
            reverse('tcms-login')+'?next=/',
            target_status_code=HTTPStatus.OK)

    def test_when_logged_in_renders_dashboard(self):
        response = self.client.get(reverse('core-views-index'))

        self.assertContains(response, _('Test executions'))
        self.assertContains(response, _('Dashboard'))
        self.assertContains(response, _('Your Test plans'))

    def test_dashboard_shows_testruns_for_manager(self):
        test_run = TestRunFactory(manager=self.tester)

        response = self.client.get(reverse('core-views-index'))
        self.assertContains(response, test_run.summary)

    def test_dashboard_shows_testruns_for_default_tester(self):
        test_run = TestRunFactory(default_tester=self.tester)

        response = self.client.get(reverse('core-views-index'))
        self.assertContains(response, test_run.summary)

    def test_dashboard_shows_testruns_for_execution_assignee(self):
        execution = TestExecutionFactory(assignee=self.tester)

        response = self.client.get(reverse('core-views-index'))
        self.assertContains(response, execution.run.summary)
