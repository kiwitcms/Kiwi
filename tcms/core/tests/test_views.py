# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors
from http import HTTPStatus

from django import test
from django.urls import include, path, reverse
from django.utils.translation import gettext_lazy as _

from tcms import urls
from tcms.tests import BaseCaseRun
from tcms.tests.factories import TestExecutionFactory, TestPlanFactory, TestRunFactory


class TestDashboard(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # used to reproduce Sentry #KIWI-TCMS-38 where rendering fails
        # with that particular value
        cls.chinese_tp = TestPlanFactory(name="缺货反馈测试需求", author=cls.tester)

    def test_when_not_logged_in_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("core-views-index"))
        self.assertRedirects(
            response,
            reverse("tcms-login") + "?next=/",
            target_status_code=HTTPStatus.OK,
        )

    def test_when_logged_in_renders_dashboard(self):
        response = self.client.get(reverse("core-views-index"))

        self.assertContains(response, _("Test executions"))
        self.assertContains(response, _("Dashboard"))
        self.assertContains(response, _("Your Test plans"))

    def test_dashboard_shows_testruns_for_manager(self):
        test_run = TestRunFactory(manager=self.tester)

        response = self.client.get(reverse("core-views-index"))
        self.assertContains(response, test_run.summary)

    def test_dashboard_shows_testruns_for_default_tester(self):
        test_run = TestRunFactory(default_tester=self.tester)

        response = self.client.get(reverse("core-views-index"))
        self.assertContains(response, test_run.summary)

    def test_dashboard_shows_testruns_for_execution_assignee(self):
        execution = TestExecutionFactory(assignee=self.tester)

        response = self.client.get(reverse("core-views-index"))
        self.assertContains(response, execution.run.summary)


def exception_view(request):
    raise Exception


urlpatterns = [
    path("will-trigger-500/", exception_view),
    path("", include(urls)),
]


handler500 = "tcms.core.views.server_error"


@test.override_settings(ROOT_URLCONF=__name__)
class TestServerError(test.TestCase):
    def test_custom_server_error_view(self):
        client = test.Client(raise_request_exception=False)
        response = client.get("/will-trigger-500/")

        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "500.html")
