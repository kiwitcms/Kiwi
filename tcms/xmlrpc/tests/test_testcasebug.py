# -*- coding: utf-8 -*-

from tcms.testcases.models import TestCaseBugSystem

from tcms.tests.factories import TestCaseRunFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestCaseBugFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCaseBugFilter, self)._fixture_setup()

        self.case_run = TestCaseRunFactory()
        self.bug_system_bz = TestCaseBugSystem.objects.get(name='Bugzilla')

        self.rpc_client.TestCaseRun.attach_bug({
            'case_run_id': self.case_run.pk,
            'bug_id': '67890',
            'bug_system_id': self.bug_system_bz.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def test_get_bugs_with_non_existing_caserun(self):
        bugs = self.rpc_client.TestCaseBug.filter({'case_run': -1})
        self.assertEqual(len(bugs), 0)
        self.assertIsInstance(bugs, list)

    def test_get_bugs_for_caserun(self):
        bugs = self.rpc_client.TestCaseBug.filter({'case_run': self.case_run.pk})
        self.assertIsNotNone(bugs)
        self.assertEqual(1, len(bugs))
        self.assertEqual(bugs[0]['summary'], 'Testing TCMS')
        self.assertEqual(bugs[0]['bug_id'], '67890')
