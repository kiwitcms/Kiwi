# pylint: disable=attribute-defined-outside-init

import os
import unittest

from tcms.issuetracker.types import Bugzilla
from tcms.rpc.tests.utils import APITestCase
from tcms.testcases.models import BugSystem
from tcms.tests.factories import TestExecutionFactory


@unittest.skipUnless(os.getenv('TEST_BUGTRACKER_INTEGRATION'),
                     'Bug tracker integration testing not enabled')
class TestBugzillaIntegration(APITestCase):
    existing_bug_id = 1
    existing_bug_url = 'http://bugtracker.kiwitcms.org/bugzilla/show_bug.cgi?id=1'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()

        bug_system = BugSystem.objects.create(  # nosec:B106:hardcoded_password_funcarg
            name='Dockerized Bugzilla',
            tracker_type='Bugzilla',
            base_url='http://bugtracker.kiwitcms.org/bugzilla/',
            api_url='http://bugtracker.kiwitcms.org/bugzilla/xmlrpc.cgi',
            api_username='admin@bugzilla.bugs',
            api_password='password',
        )
        self.integration = Bugzilla(bug_system)

    def test_bug_id_from_url(self):
        result = self.integration.bug_id_from_url(self.existing_bug_url)
        self.assertEqual(self.existing_bug_id, result)

    def test_details(self):
        result = self.integration.details(self.existing_bug_url)

        # Bugzilla doesn't support OpenGraph and ATM we don't provide
        # additional integration here
        # warning:    this vvv is not the regular - (dash) character
        self.assertEqual('1 – Hello World', result['title'])
        self.assertEqual('', result['description'])
        self.assertEqual('', result['image'])

    def test_auto_update_bugtracker(self):
        bug = self.integration.rpc.getbug(self.existing_bug_id)

        # make sure there are no comments to confuse the test
        for comment in bug.getcomments():
            self.assertNotIn('Confirmed via test execution', comment['text'])

        # simulate user adding a new bug URL to a TE and clicking
        # 'Automatically update bug tracker'
        self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution_1.pk,
            'is_defect': True,
            'url': self.existing_bug_url,
        }, True)

        # assert that a comment has been added as the last one
        # and also verify its text
        last_comment = bug.getcomments()[-1]
        for expected_string in [
                'Confirmed via test execution',
                "TR-%d: %s" % (self.execution_1.run_id, self.execution_1.run.summary),
                self.execution_1.run.get_absolute_url(),
                "TE-%d: %s" % (self.execution_1.pk, self.execution_1.case.summary)]:
            self.assertIn(expected_string, last_comment['text'])
