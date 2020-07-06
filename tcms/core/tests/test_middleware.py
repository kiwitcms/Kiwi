import os
import unittest
from django import test
from django.core.management import call_command


@unittest.skipUnless(
    os.getenv('TEST_CHECK_UNAPPLIED_MIGRATIONS_MIDDLEWARE'),
    'CheckUnappliedMigrationsMiddleware testing not enabled')
class TestCheckUnappliedMigrationsMiddleware(test.TransactionTestCase):
    def test_unapplied_migrations(self):
        call_command('migrate', 'bugs', 'zero', verbosity=2, interactive=False)
        unapplied_migration_message = 'unapplied migration(s). See '\
            '<a href="https://kiwitcms.readthedocs.io/en/latest/'\
            'installing_docker.html#initial-configuration-of-running-'\
            'container">documentation</a>'
        response = self.client.get('/', follow=True)
        self.assertContains(response, unapplied_migration_message)
