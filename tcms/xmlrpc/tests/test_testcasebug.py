# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init

from xmlrpc.client import ProtocolError
from xmlrpc.client import Fault as XmlRPCFault

from tcms.testcases.models import BugSystem

from tcms.tests.factories import TestCaseRunFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class BugFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(BugFilter, self)._fixture_setup()

        self.case_run = TestCaseRunFactory()
        self.bug_system_bz = BugSystem.objects.get(name='Bugzilla')

        self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            'case_run_id': self.case_run.pk,
            'bug_id': '67890',
            'bug_system_id': self.bug_system_bz.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def test_get_bugs_with_non_existing_caserun(self):
        bugs = self.rpc_client.exec.Bug.filter({'case_run': -1})
        self.assertEqual(len(bugs), 0)
        self.assertIsInstance(bugs, list)

    def test_get_bugs_for_caserun(self):
        bugs = self.rpc_client.exec.Bug.filter({'case_run': self.case_run.pk})
        self.assertIsNotNone(bugs)
        self.assertEqual(1, len(bugs))
        self.assertEqual(bugs[0]['summary'], 'Testing TCMS')
        self.assertEqual(bugs[0]['bug_id'], '67890')


class BugCreate(XmlrpcAPIBaseTest):
    def _fixture_setup(self):
        super(BugCreate, self)._fixture_setup()

        self.case_run = TestCaseRunFactory()
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


class BugDelete(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(BugDelete, self)._fixture_setup()

        self.bug_system_bz = BugSystem.objects.get(name='Bugzilla')
        self.bug_system_jira = BugSystem.objects.get(name='JIRA')
        self.case_run = TestCaseRunFactory()

    def setUp(self):
        super(BugDelete, self).setUp()

        self.bug_id = '67890'
        self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            'case_run_id': self.case_run.pk,
            'bug_id': self.bug_id,
            'bug_system_id': self.bug_system_bz.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

        self.jira_key = 'AWSDF-112'
        self.rpc_client.exec.Bug.create({
            'case_id': self.case_run.case.pk,
            'case_run_id': self.case_run.pk,
            'bug_id': self.jira_key,
            'bug_system_id': self.bug_system_jira.pk,
            'summary': 'Testing TCMS',
            'description': 'Just foo and bar',
        })

    def tearDown(self):
        self.case_run.case.case_bug.all().delete()
        super(BugDelete, self).tearDown()

    def test_detach_bug_with_non_exist_id(self):
        original_links_count = self.case_run.case.case_bug.count()
        self.rpc_client.exec.Bug.remove({
            'case_run_id': 9999999,
            'bug_id': 123456,
        })
        self.assertEqual(original_links_count, self.case_run.case.case_bug.count())

    def test_detach_bug_with_non_exist_bug(self):
        original_links_count = self.case_run.case.case_bug.count()
        nonexisting_bug = '{0}111'.format(self.bug_id)
        self.rpc_client.exec.Bug.remove({
            'case_run_id': self.case_run.pk,
            'bug_id': nonexisting_bug,
        })
        self.assertEqual(original_links_count, self.case_run.case.case_bug.count())

    def test_detach_bug(self):
        self.rpc_client.exec.Bug.remove({
            'case_run_id': self.case_run.pk,
            'bug_id': self.bug_id,
        })
        self.assertFalse(self.case_run.case.case_bug.filter(bug_id=self.bug_id).exists())

    def test_detach_bug_with_no_perm(self):
        self.rpc_client.exec.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.exec.Bug.remove({
                'case_run_id': self.case_run.pk,
                'bug_id': self.bug_id,
            })
