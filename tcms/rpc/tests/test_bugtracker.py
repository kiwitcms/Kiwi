# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used
#
# Copyright (c) 2025 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html


from tcms.rpc.tests.utils import APIPermissionsTestCase
from tcms.testcases.models import BugSystem
from tcms.xmlrpc_wrapper import XmlRPCFault


class BugTrackerCreate(APIPermissionsTestCase):
    permission_label = "testcases.add_bugsystem"

    def verify_api_with_permission(self):
        result = self.rpc_client.BugTracker.create(
            {
                "name": "Our Bugzilla instance",
                "tracker_type": "tcms.issuetracker.types.Bugzilla",
                "base_url": "http://example.com/bugzilla/",
                "api_url": "http://example.com/bugzilla/xmlrpc.cgi",
                "api_username": "bugzilla-bot",
                "api_password": "this-is-secret",  # nosec:B105:hardcoded_password_string
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], "Our Bugzilla instance")
        self.assertEqual(result["tracker_type"], "tcms.issuetracker.types.Bugzilla")
        self.assertEqual(result["base_url"], "http://example.com/bugzilla/")
        self.assertEqual(result["api_url"], "http://example.com/bugzilla/xmlrpc.cgi")
        self.assertEqual(result["api_username"], "bugzilla-bot")
        self.assertNotIn("api_password", result)

        # verify the object from the DB
        bug_system = BugSystem.objects.get(pk=result["id"])
        self.assertEqual(bug_system.name, result["name"])
        self.assertEqual(bug_system.tracker_type, result["tracker_type"])
        self.assertEqual(bug_system.base_url, result["base_url"])
        self.assertEqual(bug_system.api_url, result["api_url"])
        self.assertEqual(bug_system.api_username, result["api_username"])

        # a second test where bug tracker doesn't need api_password
        result = self.rpc_client.BugTracker.create(
            {
                "name": "Local Kiwi TCMS",
                "tracker_type": "tcms.issuetracker.types.KiwiTCMS",
                "base_url": "https://example.com",
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], "Local Kiwi TCMS")
        self.assertEqual(result["tracker_type"], "tcms.issuetracker.types.KiwiTCMS")
        self.assertEqual(result["base_url"], "https://example.com")
        self.assertIsNone(result["api_url"])
        self.assertIsNone(result["api_username"])
        self.assertNotIn("api_password", result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "BugTracker.create"'
        ):
            self.rpc_client.BugTracker.create(
                {
                    "name": "JIRA at kiwitcms.atlassian.net",
                    "tracker_type": "tcms.issuetracker.types.JIRA",
                    "base_url": "https://kiwitcms.atlassian.net",
                    "api_username": "hello-world",
                    "api_password": "this-is-secret",  # nosec:B105:hardcoded_password_string
                }
            )


class TestBugTrackerFilter(APIPermissionsTestCase):
    permission_label = "testcases.view_bugsystem"

    def verify_api_with_permission(self):
        result = self.rpc_client.BugTracker.filter(
            {
                "name": "Bugzilla",
            }
        )[0]

        self.assertIn("id", result)
        self.assertEqual(result["name"], "Bugzilla")
        self.assertIn("tracker_type", result)
        self.assertIn("base_url", result)
        self.assertIn("api_url", result)
        self.assertIn("api_username", result)
        self.assertNotIn("api_password", result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "BugTracker.filter"'
        ):
            self.rpc_client.BugTracker.filter({})
