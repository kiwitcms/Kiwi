# Copyright (c) 2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.conf import settings
from django.test import TestCase

from tcms import __version__
from tcms.utils.settings import import_local_settings


class ImportLocalSettingsTestCase(TestCase):
    def test_import_works(self):
        # assert default settings not changed before import
        self.assertEqual(settings.KIWI_VERSION, __version__)
        self.assertIsNone(getattr(settings, 'KIWI_MARKETPLACE', None))
        self.assertNotIn('test_me', settings.INSTALLED_APPS)

        # perform the import which will override settings
        import_local_settings('local_settings_test')

        # assert settings values have changed
        self.assertEqual(settings.KIWI_VERSION, "%s-Under-Test" % __version__)
        self.assertEqual(settings.KIWI_MARKETPLACE, 'newly-added-setting')
        self.assertIn('test_me', settings.INSTALLED_APPS)
