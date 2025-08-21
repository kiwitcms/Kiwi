# pylint: disable=attribute-defined-outside-init

import os
import time
import unittest

from django.test import override_settings

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.types import Redmine
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem
from tcms.tests.factories import ComponentFactory, TestExecutionFactory


@unittest.skipUnless(
    os.getenv("TEST_BUGTRACKER_INTEGRATION"),
    "Bug tracker integration testing not enabled",
)
@override_settings(
    EXTERNAL_ISSUE_POST_PROCESSORS=[
        "tcms.issuetracker.tests.redmine_post_processing.change_assignee"
    ]
)
class TestRedmineIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = "http://bugtracker.kiwitcms.org:3000/issues/1"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution_1 = TestExecutionFactory()
        cls.execution_1.case.save()  # will generate history object

        # this is the name of the Redmine Project
        cls.execution_1.build.version.product.name = "Integration with Kiwi TCMS"
        cls.execution_1.build.version.product.save()

        cls.component = ComponentFactory(
            name="Redmine integration", product=cls.execution_1.run.plan.product
        )
        cls.execution_1.case.add_component(cls.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="Redmine at kiwitcms.atlassian.net",
            tracker_type="tcms.issuetracker.types.Redmine",
            base_url="http://bugtracker.kiwitcms.org:3000",
            api_username="admin",
            api_password="admin",
        )
        cls.integration = Redmine(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details_for_url(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual(self.existing_bug_id, result["id"])
        self.assertEqual("Created via API", result["description"])
        self.assertEqual("OPEN", result["status"])
        self.assertEqual("Hello Redmine", result["title"])
        self.assertEqual(self.existing_bug_url, result["url"])

    def test_auto_update_bugtracker(self):
        issue = self.integration.rpc.issue.get(self.existing_bug_id)

        # make sure there are no comments to confuse the test
        initial_comments_count = 0
        for comment in issue.journals:
            initial_comments_count += 1
            self.assertNotIn(self.execution_1.run.summary, comment.notes)

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        result = self.rpc_client.TestExecution.add_link(
            {
                "execution_id": self.execution_1.pk,
                "is_defect": True,
                "url": self.existing_bug_url,
            },
            True,
        )

        # making sure RPC above returned the same URL
        self.assertEqual(self.existing_bug_url, result["url"])

        # wait until comments have been refreshed b/c this seem to happen async
        retries = 0
        current_comment_count = 0
        while current_comment_count <= initial_comments_count:
            # fetch the issue again to refresh the journal
            issue = self.integration.rpc.issue.get(self.existing_bug_id)
            current_comment_count = len(issue.journals)
            time.sleep(1)
            retries += 1
            self.assertLess(retries, 20)

        # this is an interator but is not a list
        last_comment = None
        for comment in issue.journals:
            last_comment = comment

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
            "Confirmed via test execution",
            f"TR-{self.execution_1.run_id}: {self.execution_1.run.summary}",
            self.execution_1.run.get_full_url(),
            f"TE-{self.execution_1.pk}: {self.execution_1.case.summary}",
        ]:
            self.assertIn(expected_string, last_comment.notes)

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(
            self.execution_1.pk, self.integration.bug_system.pk
        )
        self.assertEqual(result["rc"], 0)
        self.assertIn(self.integration.bug_system.base_url, result["response"])
        self.assertIn("http://bugtracker.kiwitcms.org:3000/issues/", result["response"])

        new_issue_id = self.integration.bug_id_from_url(result["response"])
        issue = self.integration.rpc.issue.get(new_issue_id)

        # this is coming from post-processing
        assignee = self.integration.rpc.user.get(issue.assigned_to.id)
        self.assertEqual(assignee.login, "atodorov")

        self.assertEqual(f"Failed test: {self.execution_1.case.summary}", issue.subject)
        for expected_string in [
            f"Filed from execution {self.execution_1.get_full_url()}",
            "Reporter",
            self.execution_1.build.version.product.name,
            self.component.name,
            "Steps to reproduce",
            self.execution_1.case.text,
        ]:
            self.assertIn(expected_string, issue.description)

        # verify that LR has been added to TE
        self.assertTrue(
            LinkReference.objects.filter(
                execution=self.execution_1,
                url=result["response"],
                is_defect=True,
            ).exists()
        )

    def test_non_overriden_credentials_are_returned(self):
        (rpc_username, rpc_password) = self.integration.rpc_credentials

        # admin:admin as defined above
        self.assertEqual(rpc_username, "admin")
        self.assertEqual(rpc_password, "admin")

    @override_settings(
        EXTERNAL_ISSUE_RPC_CREDENTIALS="tcms.issuetracker.tests.redmine_post_processing.rpc_creds"
    )
    def test_overriden_credentials_are_returned(self):
        (rpc_username, rpc_password) = self.integration.rpc_credentials

        # not admin:admin as defined above
        self.assertEqual(rpc_username, "tester")
        self.assertEqual(rpc_password, "test-me")

    @override_settings(
        EXTERNAL_ISSUE_RPC_CREDENTIALS="tcms.issuetracker.tests.redmine_post_processing.rpc_no_creds"
    )
    def test_overriden_credentials_fallback(self):
        (rpc_username, rpc_password) = self.integration.rpc_credentials

        # admin:admin as defined above b/c rpc_no_creds() returns None
        self.assertEqual(rpc_username, "admin")
        self.assertEqual(rpc_password, "admin")

    def test_auth_with_api_key_only_works(self):
        """
        Verify API-key-only auth path: empty username + api_password == API key.
        The admin API key is fixed in Redmine seeds.rb.
        """
        fixed_key = "0123456789abcdef0123456789abcdef01234567"

        bug_system_token = BugSystem.objects.create(  # nosec:B106
            name="Redmine (token-only)",
            tracker_type="tcms.issuetracker.types.Redmine",
            base_url="http://bugtracker.kiwitcms.org:3000",
            api_username="",  # empty -> treat api_password as API access key
            api_password=fixed_key,  # seeded fixed key
        )
        token_integration = Redmine(bug_system_token, None)

        # If token auth works, details() should succeed and return the known data.
        details = token_integration.details(self.existing_bug_url)

        self.assertEqual(self.existing_bug_id, details["id"])
        self.assertEqual("Created via API", details["description"])
        self.assertEqual("OPEN", details["status"])
        self.assertEqual("Hello Redmine", details["title"])
        self.assertEqual(self.existing_bug_url, details["url"])
