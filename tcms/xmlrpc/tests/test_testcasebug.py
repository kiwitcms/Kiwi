# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init

from xmlrpc.client import ProtocolError
from xmlrpc.client import Fault as XmlRPCFault

from tcms.testcases.models import BugSystem

from tcms.tests.factories import TestExecutionFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class BugFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(BugFilter, self)._fixture_setup()

        self.execution = TestExecutionFactory()
        self.bug_system_bz = BugSystem.objects.get(name='Bugzilla')

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


class BugCreate(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(BugCreate, self)._fixture_setup()

        self.case_run = TestExecutionFactory()
        self.bug_system_jira = BugSystem.objects.get(name='JIRA')
        self.bug_system_bz = BugSystem.objects.get(name='Bugzilla')

    def test_attach_bug_with_no_perm(self):
        self.rpc_client.exec.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.exec.Bug.create({})

    def test_attach_bug_with_no_required_args(self):
        values = [
            {
                "summary": "This is summary.",
                "description": "This is description."
            },
            {
                "description": "This is description."
            },
            {
                "summary": "This is summary.",
            },
        ]
        for value in values:
            with self.assertRaises(XmlRPCFault):
                self.rpc_client.exec.Bug.create(value)

    def test_attach_bug_with_required_args(self):
        bug = self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            "case_run_id": self.case_run.pk,
            "bug_id": '1',
            "bug_system_id": self.bug_system_bz.pk,
        })
        self.assertIsNotNone(bug)

        bug = self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            "case_run_id": self.case_run.pk,
            "bug_id": "TCMS-123",
            "bug_system_id": self.bug_system_jira.pk,
        })
        self.assertIsNotNone(bug)

    def test_attach_bug_with_all_fields(self):
        bug = self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            "case_run_id": self.case_run.pk,
            "bug_id": '2',
            "bug_system_id": self.bug_system_bz.pk,
            "summary": "This is summary.",
            "description": "This is description."
        })
        self.assertIsNotNone(bug)

    def test_attach_bug_with_non_existing_case_run(self):
        value = {
            'case_id': self.case_run.case.pk,
            "case_run_id": -1,
            "bug_id": '2',
            "bug_system_id": self.bug_system_bz.pk,
        }
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.exec.Bug.create(value)

    def test_attach_bug_with_non_existing_bug_system(self):
        value = {
            "case_run_id": self.case_run.pk,
            "bug_id": '2',
            "bug_system_id": -1,
        }
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.exec.Bug.create(value)

    def test_attach_bug_with_chinese(self):
        bug = self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            "case_run_id": self.case_run.pk,
            "bug_id": '12',
            "bug_system_id": self.bug_system_bz.pk,
            "summary": u"你好，中国",
            "description": u"中国是一个具有悠久历史的文明古国"
        })
        self.assertIsNotNone(bug)
