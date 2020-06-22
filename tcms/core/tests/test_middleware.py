import os
import unittest
from django import test
from django.conf import settings
from django.apps import apps
from django.contrib.messages import get_messages


@unittest.skipUnless(
    os.getenv('TEST_CHECK_UNAPPLIED_MIGRATIONS_MIDDLEWARE'),
    'CheckUnappliedMigrationsMiddleware testing not enabled')
class TestCheckUnappliedMigrationsMiddleware(test.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.INSTALLED_APPS.append("tcms.core.tests.test_migrations_app")
        apps.set_installed_apps(settings.INSTALLED_APPS)

    @test.override_settings(MIGRATION_MODULES={
        "migrations": "tcms.core.tests.test_migrations_app.migrations"})
    def test_unapplied_migrations(self):
        unapplied_migration_message = """You have 1 unapplied migration(s).\
 See <a href="https://kiwitcms.readthedocs.io/en/latest/installing_docker.html\
#initial-configuration-of-running-container">documentation</a>"""
        response = self.client.get('/', follow=True)
        self.assertContains(response, unapplied_migration_message)
