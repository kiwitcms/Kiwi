# pylint: disable=attribute-defined-outside-init

import unittest

from django.conf import settings
from django.core.cache import cache
from django.test import RequestFactory, override_settings
from mock import MagicMock, patch

from tcms.rpc.api import utils
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem

if "tcms.bugs.apps.AppConfig" not in settings.INSTALLED_APPS:
    raise unittest.SkipTest("tcms.bugs is disabled")


class TestBug(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        cls.url = "http://some.url"
        cls.expected_result = {
            "title": "Bug from cache",
            "description": "This bug came from the Django cache",
        }

        BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="Bugzilla Org",
            tracker_type="tcms.issuetracker.types.Bugzilla",
            base_url="http://bugzilla.org",
            api_url="http://bugzilla.org/xmlrpc.cgi",
            api_username="admin@bugzilla.bugs",
            api_password="password",
        )

    @patch("tcms.rpc.api.bug.tracker_from_url")
    def test_get_details_from_tracker(self, tracker_from_url):
        returned_tracker = MagicMock()
        returned_tracker.details.return_value = self.expected_result
        tracker_from_url.return_value = returned_tracker

        result = self.rpc_client.Bug.details(self.url)

        self.assertEqual(result, self.expected_result)
        returned_tracker.details.assert_called_once_with(self.url)

    # override the cache settings, because by default we are using DummyCache,
    # which satisfies the interface, but does no caching
    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "kiwitcms",
                "TIMEOUT": 3600,
            }
        }
    )
    @patch("tcms.rpc.api.bug.tracker_from_url")
    def test_get_details_from_cache(self, tracker_from_url):
        cache.set(self.url, self.expected_result)

        result = self.rpc_client.Bug.details(self.url)

        self.assertEqual(result, self.expected_result)
        tracker_from_url.assert_not_called()

    def test_empty_details_when_tracker_does_not_exist(self):
        url = "http://unknown-tracker.url"

        result = self.rpc_client.Bug.details(url)
        self.assertEqual(result, {})

    def test_tracker_from_url_returns_instance_when_match(self):
        tracker = utils.tracker_from_url(
            "http://bugzilla.org/show_bug.cgi?id=123456", RequestFactory()
        )
        self.assertIsNotNone(tracker)

    def test_tracker_from_url_returns_none_when_dont_match(self):
        tracker = utils.tracker_from_url(
            "http://bugzilla.org.kiwitcms.eu/show_bug.cgi?id=123456",
            RequestFactory(),
        )
        self.assertIsNone(tracker)
