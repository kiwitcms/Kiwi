# pylint: disable=attribute-defined-outside-init

import unittest
from mock import patch, MagicMock

from django.conf import settings
from django.core.cache import cache
from django.test import override_settings

from tcms.rpc.tests.utils import APITestCase

if 'tcms.bugs.apps.AppConfig' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest('tcms.bugs is disabled')


class TestBug(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()
        self.url = "http://some.url"
        self.expected_result = {
            'title': 'Bug from cache',
            'description': 'This bug came from the Django cache'
        }

    @patch('tcms.rpc.api.bug.tracker_from_url')
    def test_get_details_from_tracker(self, tracker_from_url):
        returned_tracker = MagicMock()
        returned_tracker.details.return_value = self.expected_result
        tracker_from_url.return_value = returned_tracker

        result = self.rpc_client.Bug.details(self.url)

        self.assertEqual(result, self.expected_result)
        returned_tracker.details.assert_called_once_with(self.url)

    # override the cache settings, because by default we are using DummyCache,
    # which satisfies the interface, but does no caching
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'kiwitcms',
            'TIMEOUT': 3600,
        }
    })
    @patch('tcms.rpc.api.bug.tracker_from_url')
    def test_get_details_from_cache(self, tracker_from_url):
        cache.set(self.url, self.expected_result)

        result = self.rpc_client.Bug.details(self.url)

        self.assertEqual(result, self.expected_result)
        tracker_from_url.assert_not_called()

    def test_empty_details_when_tracker_does_not_exist(self):
        url = "http://unknown-tracker.url"

        result = self.rpc_client.Bug.details(url)
        self.assertEqual(result, {})
