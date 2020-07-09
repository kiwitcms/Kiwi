# pylint: disable=attribute-defined-outside-init

import os
import time
import unittest

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.types import Redmine
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import TestExecutionFactory


@unittest.skipUnless(os.getenv('TEST_BUGTRACKER_INTEGRATION'),
                     'Bug tracker integration testing not enabled')
class TestRedmineIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = 'http://bugtracker.kiwitcms.org:3000/issues/1'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_1.case.save()  # will generate history object

        # this is the name of the Redmine Project
        self.execution_1.run.plan.product.name = 'Integration with Kiwi TCMS'
        self.execution_1.run.plan.product.save()

        self.component = ComponentFactory(name='Redmine integration',
                                          product=self.execution_1.run.plan.product)
        self.execution_1.case.add_component(self.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='Redmine at kiwitcms.atlassian.net',
            tracker_type='tcms.issuetracker.types.Redmine',
            base_url='http://bugtracker.kiwitcms.org:3000',
            api_username='admin',
            api_password='admin',
        )
        self.integration = Redmine(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details_for_url(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual('Hello Redmine', result['title'])
        self.assertEqual('Created via API', result['description'])

    def test_auto_update_bugtracker(self):
        issue = self.integration.rpc.issue.get(self.existing_bug_id)

        # make sure there are no comments to confuse the test
        initial_comments_count = 0
        for comment in issue.journals:
            initial_comments_count += 1
            self.assertNotIn(self.execution_1.run.summary, comment.notes)

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
                'Confirmed via test execution',
                "TR-%d: %s" % (self.execution_1.run_id, self.execution_1.run.summary),
                self.execution_1.run.get_full_url(),
                "TE-%d: %s" % (self.execution_1.pk, self.execution_1.case.summary)]:
            self.assertIn(expected_string, last_comment.notes)

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(self.execution_1.pk, self.integration.bug_system.pk)
        self.assertEqual(result['rc'], 0)
        self.assertIn(self.integration.bug_system.base_url, result['response'])
        self.assertIn('http://bugtracker.kiwitcms.org:3000/issues/', result['response'])

        new_issue_id = self.integration.bug_id_from_url(result['response'])
        issue = self.integration.rpc.issue.get(new_issue_id)

        self.assertEqual("Failed test: %s" % self.execution_1.case.summary, issue.subject)
        for expected_string in [
                "Filed from execution %s" % self.execution_1.get_full_url(),
                self.execution_1.run.plan.product.name,
                self.component.name,
                "Steps to reproduce",
                self.execution_1.case.text]:
            self.assertIn(expected_string, issue.description)

        # verify that LR has been added to TE
        self.assertTrue(LinkReference.objects.filter(
            execution=self.execution_1,
            url=result['response'],
            is_defect=True,
        ).exists())
