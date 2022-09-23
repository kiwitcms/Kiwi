# pylint: disable=attribute-defined-outside-init
import os
import unittest

from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.mantis import Mantis, MantisAPI
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem
from tcms.tests.factories import ComponentFactory, TestExecutionFactory


@unittest.skipUnless(
    os.getenv("TEST_BUGTRACKER_INTEGRATION"),
    "Bug tracker integration testing not enabled",
)
class TestMantisIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = "http://localhost/rest/api/issues/1"
    mantis_project = "Sample_Project"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_1.case.summary = "Tested at " + timezone.now().isoformat()
        self.execution_1.case.text = "Given-When-Then"
        self.execution_1.case.save()  # will generate history object
        self.execution_1.run.summary = (
            "Automated TR for Mantis integration on " + timezone.now().isoformat()
        )
        self.execution_1.run.save()

        self.component = ComponentFactory(
            name="Mantis integration", product=self.execution_1.run.plan.product
        )
        self.execution_1.case.add_component(self.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="Mantis for kiwitcms/test-mantis-integration",
            tracker_type="tcms.issuetracker.mantis.Mantis",
            base_url="http://localhost",
            api_url=self.mantis_project,
            api_password=os.getenv("MANTIS_INTEGRATION_API_PASSWORD"),
        )
        self.integration = Mantis(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual("Hello World", result["title"])
        self.assertIn("First public bug here", result["description"])

    def test_auto_update_bugtracker(self):
        initial_comments = self.integration.rpc.get_comments(self.existing_bug_id)

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
        initial_comments_length = len(initial_comments)
        current_comments_length = initial_comments_length
        while current_comments_length != initial_comments_length + 1:
            comments = self.integration.rpc.get_comments(self.existing_bug_id)
            current_comments_length = len(comments)

        last_comment = comments[-1]

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
            "Confirmed via test execution",
            f"TR-{self.execution_1.run_id}: {self.execution_1.run.summary}",
            self.execution_1.run.get_full_url(),
            f"TE-{self.execution_1.pk}: {self.execution_1.case.summary}",
        ]:
            self.assertIn(expected_string, last_comment["text"])

        self.integration.rpc.delete_comment(self.existing_bug_id, last_comment["id"])

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(
            self.execution_1.pk, self.integration.bug_system.pk
        )
        self.assertEqual(result["rc"], 0)
        self.assertIn(self.integration.bug_system.base_url, result["response"])
        self.assertIn("view.php?id=", result["response"])

        new_issue_id = self.integration.bug_id_from_url(result["response"])
        issue = self.integration.rpc.get_issue(new_issue_id)["issues"][0]

        self.assertEqual(
            f"Failed test: {self.execution_1.case.summary}", issue["summary"]
        )
        for expected_string in [
            f"Filed from execution {self.execution_1.get_full_url()}",
            "Reporter",
            self.execution_1.run.plan.product.name,
            self.component.name,
            "Steps to reproduce",
            self.execution_1.case.text,
        ]:
            self.assertIn(expected_string, issue["description"])

        # verify that LR has been added to TE
        self.assertTrue(
            LinkReference.objects.filter(
                execution=self.execution_1,
                url=result["response"],
                is_defect=True,
            ).exists()
        )

        # Close issue after test is finised.
        close_issue(self.integration.rpc, new_issue_id)

    def test_report_issue_from_test_execution_empty_baseurl_exception(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name="Mantis for kiwitcms/test-mantis-integration Exception",
            tracker_type="tcms.issuetracker.mantis.Mantis",
            base_url="incorrect_url",
            api_password=os.getenv("MANTIS_INTEGRATION_API_PASSWORD"),
        )
        integration = Mantis(bug_system, None)
        result = self.rpc_client.Bug.report(
            self.execution_1.pk, integration.bug_system.pk
        )
        self.assertIn("bug_report_page.php", result["response"])


@unittest.skipUnless(
    os.getenv("TEST_BUGTRACKER_INTEGRATION"),
    "Bug tracker integration testing not enabled",
)
class TestMantisAPI(unittest.TestCase):
    mantis_project = "Sample_Project"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client_secret = os.getenv("MANTIS_INTEGRATION_API_PASSWORD")
        base_url = "http://localhost"
        cls.api_instance = MantisAPI(base_url, client_secret)

        test_issue_data = {
            "summary": "Sample Issue",
            "description": "Sample Issue Description",
            "category": {"name": "General"},
            "project": {"name": cls.mantis_project},
        }

        result = cls.api_instance.create_issue(test_issue_data)
        cls.issue_id = result["issue"]["id"]

    @classmethod
    def tearDownClass(cls):
        close_issue(cls.api_instance, cls.issue_id)
        return super().tearDownClass()

    def test_create_issue(self):
        test_issue_data = {
            "summary": "Sample Issue",
            "description": "Sample Issue Description",
            "category": {"name": "General"},
            "project": {"name": self.mantis_project},
        }

        result = self.api_instance.create_issue(test_issue_data)
        self.assertEqual(result["issue"]["summary"], "Sample Issue")

        # Close work item after test is finished.
        close_issue(self.api_instance, result["issue"]["id"])

    def test_add_comment(self):
        test_comment_body = {"text": "Test Comment"}
        result = self.api_instance.add_comment(self.issue_id, test_comment_body)
        self.assertEqual(result["note"]["text"], "Test Comment")
        self.api_instance.delete_comment(self.issue_id, result["note"]["id"])


def close_issue(instance, issue_id):
    close_issue_body = {"status": {"name": "closed"}}
    instance.update_issue(issue_id, close_issue_body)
