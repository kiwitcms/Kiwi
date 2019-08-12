# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init

from tcms.testcases.models import BugSystem

from tcms.tests.factories import TestExecutionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class BugFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(BugFilter, self)._fixture_setup()

        self.execution = TestExecutionFactory()
        self.bug_system_bz = BugSystem.objects.get(name='Bugzilla')

        # TODO: this needs to be replaced with TestExecution.add_link()
        self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            'case_run_id': self.execution.pk,
            'bug_id': '67890',
            'bug_system_id': self.bug_system_bz.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def test_get_bugs_with_non_existing_caserun(self):
        bugs = self.rpc_client.exec.Bug.filter({'execution': -1})
        self.assertEqual(len(bugs), 0)
        self.assertIsInstance(bugs, list)

    def test_get_bugs_for_caserun(self):
        bugs = self.rpc_client.exec.Bug.filter({'execution': self.execution.pk})
        self.assertIsNotNone(bugs)
        self.assertEqual(1, len(bugs))
        self.assertEqual(bugs[0]['summary'], 'Testing TCMS')
        self.assertEqual(bugs[0]['bug_id'], '67890')
