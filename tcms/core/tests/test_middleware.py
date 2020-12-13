import os
import unittest

from django import test
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


@unittest.skipUnless(
    os.getenv("TEST_CHECK_UNAPPLIED_MIGRATIONS_MIDDLEWARE"),
    "CheckUnappliedMigrationsMiddleware testing not enabled",
)
class TestCheckUnappliedMigrationsMiddleware(test.TransactionTestCase):
    def test_unapplied_migrations(self):
        call_command("migrate", "bugs", "zero", verbosity=2, interactive=False)
        unapplied_migration_message = _(
            "unapplied migration(s). See "
            '<a href="https://kiwitcms.readthedocs.io/en/latest/'
            "installing_docker.html#initial-configuration-of-running-"
            'container">documentation</a>'
        )
        response = self.client.get("/", follow=True)
        self.assertContains(response, unapplied_migration_message)


class TestCheckSettingsMiddleware(test.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        doc_url = "https://kiwitcms.readthedocs.io/en/latest/admin.html#configure-kiwi-s-base-url"
        cls.base_url_error_message = _(
            "Base URL is not configured! "
            'See <a href="%(doc_url)s">documentation</a> and '
            '<a href="%(admin_url)s">change it</a>'
        ) % {
            "doc_url": doc_url,
            "admin_url": reverse("admin:sites_site_change", args=[settings.SITE_ID]),
        }

    def test_base_url_not_configured(self):
        response = self.client.get("/", follow=True)
        self.assertContains(response, self.base_url_error_message)

    def test_base_url_configured(self):
        site = Site.objects.create(domain="example.com", name="example")
        with test.override_settings(SITE_ID=site.pk):
            response = self.client.get("/", follow=True)
            self.assertNotContains(response, self.base_url_error_message)
