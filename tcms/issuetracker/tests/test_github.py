# pylint: disable=attribute-defined-outside-init

import os
import time
import unittest

from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.types import GitHub
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import TestExecutionFactory


@unittest.skipUnless(os.getenv('TEST_BUGTRACKER_INTEGRATION'),
                     'Bug tracker integration testing not enabled')
class TestGitHubIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = 'https://github.com/kiwitcms/test-github-integration/issues/1'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_1.case.summary = "Tested at " + timezone.now().isoformat()
        self.execution_1.case.text = "Given-When-Then"
        self.execution_1.case.save()  # will generate history object
        self.execution_1.run.summary = "Automated TR for GitHub integration on " + \
                                       timezone.now().isoformat()
        self.execution_1.run.save()

        self.component = ComponentFactory(name='GitHub integration',
                                          product=self.execution_1.run.plan.product)
        self.execution_1.case.add_component(self.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='GitHub for kiwitcms/test-github-integration',
            tracker_type='tcms.issuetracker.types.GitHub',
            base_url='https://github.com/kiwitcms/test-github-integration',
            api_password=os.getenv('GH_BUGTRACKER_INTEGRATION_TEST_API_TOKEN'),
        )
        self.integration = GitHub(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details_for_public_url(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual('Hello GitHub', result['title'])
        self.assertEqual(
            "This issue is used in automated tests that verify Kiwi TCMS - GitHub "
            "bug tracking integration!",
            result['description'])

    def test_details_for_private_url(self):
        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='Private GitHub for kiwitcms/private-test-github-integration',
            tracker_type='GitHub',
            base_url='https://github.com/kiwitcms/private-test-github-integration',
            api_password=os.getenv('GH_BUGTRACKER_INTEGRATION_TEST_API_TOKEN'),
        )
        integration = GitHub(bug_system, None)

        result = integration.details(
            'https://github.com/kiwitcms/private-test-github-integration/issues/1')

        self.assertEqual('Hello Private GitHub', result['title'])
        self.assertEqual(
            "This issue is used in automated tests that verify "
            "Kiwi TCMS - GitHub bug tracking integration!",
            result['description'])

    def test_auto_update_bugtracker(self):
        repo_id = self.integration.it_class.repo_id(self.integration.bug_system)
        repo = self.integration.rpc.get_repo(repo_id)
        issue = repo.get_issue(self.existing_bug_id)

        # make sure there are no comments to confuse the test
        initial_comments_count = 0
        for comment in issue.get_comments():
            initial_comments_count += 1
            self.assertNotIn(self.execution_1.run.summary, comment.body)

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        result = self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution_1.pk,
            'is_defect': True,
            'url': self.existing_bug_url,
        }, True)

        # making sure RPC above returned the same URL
        self.assertEqual(self.existing_bug_url, result['url'])

        # wait until comments have been refreshed b/c this seem to happen async
        retries = 0
        last_comment = None
        current_comment_count = 0
        while current_comment_count <= initial_comments_count:
            current_comment_count = 0
            # .get_comments() returns an iterator
            for comment in issue.get_comments():
                current_comment_count += 1
                last_comment = comment

            time.sleep(1)
            retries += 1
            self.assertLess(retries, 20)

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
                'Confirmed via test execution',
                "TR-%d: %s" % (self.execution_1.run_id, self.execution_1.run.summary),
                self.execution_1.run.get_full_url(),
                "TE-%d: %s" % (self.execution_1.pk, self.execution_1.case.summary)]:
            self.assertIn(expected_string, last_comment.body)

        # clean up after ourselves in case everything above looks good
        last_comment.delete()

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(self.execution_1.pk, self.integration.bug_system.pk)
        self.assertEqual(result['rc'], 0)
        self.assertIn(self.integration.bug_system.base_url, result['response'])
        self.assertIn('/issues/', result['response'])

        new_issue_id = self.integration.bug_id_from_url(result['response'])
        repo_id = self.integration.it_class.repo_id(self.integration.bug_system)
        repo = self.integration.rpc.get_repo(repo_id)
        issue = repo.get_issue(new_issue_id)

        self.assertEqual("Failed test: %s" % self.execution_1.case.summary, issue.title)
        for expected_string in [
                "Filed from execution %s" % self.execution_1.get_full_url(),
                self.execution_1.run.plan.product.name,
                self.component.name,
                "Steps to reproduce",
                self.execution_1.case.text]:
            self.assertIn(expected_string, issue.body)

        # verify that LR has been added to TE
        self.assertTrue(LinkReference.objects.filter(
            execution=self.execution_1,
            url=result['response'],
            is_defect=True,
        ).exists())

        # close issue after we're done
        issue.edit(state='closed')
