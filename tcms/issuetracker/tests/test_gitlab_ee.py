# pylint: disable=attribute-defined-outside-init

import os
import time
import unittest

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.issuetracker.types import Gitlab
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem

from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import TestExecutionFactory


@unittest.skipUnless(os.getenv('TEST_BUGTRACKER_INTEGRATION'),
                     'Bug tracker integration testing not enabled')
class TestGitlabIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = 'http://bugtracker.kiwitcms.org/root/kiwitcms/issues/1'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_1.case.text = "Given-When-Then"
        self.execution_1.case.save()  # will generate history object

        self.component = ComponentFactory(name='Gitlab integration',
                                          product=self.execution_1.run.plan.product)
        self.execution_1.case.add_component(self.component)

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='GitLab-EE for root/kiwitcms',
            tracker_type='tcms.issuetracker.types.Gitlab',
            base_url='http://bugtracker.kiwitcms.org/root/kiwitcms/',
            api_url='http://bugtracker.kiwitcms.org',
            api_password='ypCa3Dzb23o5nvsixwPA',
        )
        self.integration = Gitlab(bug_system, None)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

        # this is an alternative URL, with a dash
        result = self.integration.bug_id_from_url(
            'http://bugtracker.kiwitcms.org/root/kiwitcms/-/issues/1')
        self.assertEqual(self.existing_bug_id, result)

    def test_details_for_public_url(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual('Hello GitLab', result['title'])
        self.assertEqual('Created via CLI', result['description'])

    def test_details_for_private_url(self):
        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='Private GitLab for root/katinar',
            tracker_type='tcms.issuetracker.types.Gitlab',
            base_url='http://bugtracker.kiwitcms.org/root/katinar/',
            api_url='http://bugtracker.kiwitcms.org',
            api_password='ypCa3Dzb23o5nvsixwPA',
        )
        integration = Gitlab(bug_system, None)

        result = integration.details('http://bugtracker.kiwitcms.org/root/katinar/-/issues/1')

        self.assertEqual('Hello Private Issue', result['title'])
        self.assertEqual('Created in secret via CLI', result['description'])

    def test_auto_update_bugtracker(self):
        repo_id = self.integration.it_class.repo_id(self.integration.bug_system)
        gl_project = self.integration.rpc.projects.get(repo_id)
        gl_issue = gl_project.issues.get(self.existing_bug_id)

        # make sure there are no comments to confuse the test
        initial_comment_count = 0
        for comment in gl_issue.notes.list():
            initial_comment_count += 1
            self.assertNotIn('Confirmed via test execution', comment.body)

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
        while len(gl_issue.notes.list()) <= initial_comment_count:
            time.sleep(1)
            retries += 1
            self.assertLess(retries, 20)

        # sort by id b/c the gitlab library returns newest comments first but
        # that may be depending on configuration !
        last_comment = sorted(gl_issue.notes.list(), key=lambda x: x.id)[-1]

        # assert that a comment has been added as the last one
        # and also verify its text
        for expected_string in [
                'Confirmed via test execution',
                "TR-%d: %s" % (self.execution_1.run_id, self.execution_1.run.summary),
                self.execution_1.run.get_full_url(),
                "TE-%d: %s" % (self.execution_1.pk, self.execution_1.case.summary)]:
            self.assertIn(expected_string, last_comment.body)

    def test_report_issue_from_test_execution_1click_works(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(self.execution_1.pk, self.integration.bug_system.pk)
        self.assertEqual(result['rc'], 0)
        self.assertIn(self.integration.bug_system.base_url, result['response'])
        self.assertIn('/-/issues/', result['response'])

        # assert that the result looks like valid URL parameters
        new_issue_id = self.integration.bug_id_from_url(result['response'])
        repo_id = self.integration.it_class.repo_id(self.integration.bug_system)
        gl_project = self.integration.rpc.projects.get(repo_id)
        issue = gl_project.issues.get(new_issue_id)

        self.assertEqual("Failed test: %s" % self.execution_1.case.summary, issue.title)
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
