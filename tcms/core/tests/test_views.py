# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors
import os
import unittest
from http import HTTPStatus

from django import test
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.urls import include, path, reverse
from django.utils.translation import gettext_lazy as _

from tcms import urls
from tcms.tests import LoggedInTestCase
from tcms.tests.factories import (
    TestExecutionFactory,
    TestPlanFactory,
    TestRunFactory,
    UserFactory,
)


class TestDashboard(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # used to reproduce Sentry #KIWI-TCMS-38 where rendering fails
        # with that particular value
        cls.chinese_tp = TestPlanFactory(name="缺货反馈测试需求", author=cls.tester)
        doc_url = (
            "https://kiwitcms.readthedocs.io/en/latest/installing_docker.html"
            "#configuration-of-kiwi-tcms-domain"
        )
        cls.base_url_error_message = _(
            "Base URL is not configured! "
            'See <a href="%(doc_url)s">documentation</a> and '
            '<a href="%(admin_url)s">change it</a>'
        ) % {
            "doc_url": doc_url,
            "admin_url": reverse("admin:sites_site_change", args=[settings.SITE_ID]),
        }

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

    def test_check_base_url_not_configured(self):
        response = self.client.get("/", follow=True)
        self.assertContains(response, self.base_url_error_message)

    def test_check_base_url_configured(self):
        site = Site.objects.create(domain="example.com", name="example")
        with test.override_settings(SITE_ID=site.pk):
            response = self.client.get("/", follow=True)
            self.assertNotContains(response, self.base_url_error_message)

    def test_check_connection_not_using_ssl(self):
        response = self.client.get("/", follow=True)
        doc_url = (
            "https://kiwitcms.readthedocs.io/en/latest/installing_docker.html"
            "#ssl-configuration"
        )
        ssl_error_message = _(
            "You are not using a secure connection. "
            'See <a href="%(doc_url)s">documentation</a> and enable SSL.'
        ) % {"doc_url": doc_url}
        self.assertContains(response, ssl_error_message)


@unittest.skipUnless(
    os.getenv("TEST_DASHBOARD_CHECK_UNAPPLIED_MIGRATIONS"),
    "Check for missing migrations testing is not enabled",
)
class TestDashboardCheckMigrations(test.TransactionTestCase):
    unapplied_migration_message = _(
        "unapplied migration(s). See "
        '<a href="https://kiwitcms.readthedocs.io/en/latest/'
        "installing_docker.html#initial-configuration-of-running-"
        'container">documentation</a>'
    )

    def test_check_unapplied_migrations(self):
        call_command("migrate", "bugs", "zero", verbosity=2, interactive=False)
        tester = UserFactory()
        tester.set_password("password")
        tester.save()
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=tester.username,
            password="password",
        )
        response = self.client.get("/", follow=True)
        self.assertContains(response, self.unapplied_migration_message)


def exception_view(request):
    raise RuntimeError


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
