# pylint: disable=attribute-defined-outside-init

import os
import time
import unittest

from tcms.issuetracker.types import Gitlab
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem

from tcms.tests.factories import TestExecutionFactory


@unittest.skipUnless(os.getenv('TEST_BUGTRACKER_INTEGRATION'),
                     'Bug tracker integration testing not enabled')
class TestGitlabIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = 'http://bugtracker.kiwitcms.org/root/kiwitcms/issues/1'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='GitLab-EE for root/kiwitcms',
            tracker_type='Gitlab',
            base_url='http://bugtracker.kiwitcms.org/root/kiwitcms/',
            api_url='http://bugtracker.kiwitcms.org',
            api_password='ypCa3Dzb23o5nvsixwPA',
        )
        self.integration = Gitlab(bug_system)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

        # this is an alternative URL, with a dash
        result = self.integration.bug_id_from_url(
            'http://bugtracker.kiwitcms.org/root/kiwitcms/-/issues/1')
        self.assertEqual(self.existing_bug_id, result)

    def test_details(self):
        result = self.integration.details(self.existing_bug_url)

        self.assertEqual('Hello GitLab (#1) · Issues · Administrator / kiwitcms',
                         result['title'])
        self.assertEqual('Created via CLI', result['description'])
        self.assertIn('/assets/gitlab_logo', result['image'])

    def test_auto_update_bugtracker(self):
        repo_slug = self.integration.repo_slug()
        gl_project = self.integration.rpc.projects.get(repo_slug)
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

    def test_report_issue_from_test_execution_falls_back_to_query_params(self):
        # simulate user clicking the 'Report bug' button in TE widget, TR page
        result = self.rpc_client.Bug.report(self.execution_1.pk, self.integration.bug_system.pk)
        self.assertEqual(result['rc'], 0)
        self.assertIn(self.integration.bug_system.base_url, result['response'])
        self.assertIn('issues/new', result['response'])

        # assert that the result looks like valid URL parameters
        self.assertIn('?issue%5Btitle%5D=Failed+test', result['response'])
        self.assertIn('&issue%5Bdescription%5D=Filed+from+execution', result['response'])
