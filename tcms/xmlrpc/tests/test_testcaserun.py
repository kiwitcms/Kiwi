# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init, objects-update-used

from xmlrpc.client import ProtocolError
from xmlrpc.client import Fault as XmlRPCFault

from datetime import datetime

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.testruns.models import TestCaseRunStatus

from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.tests.factories import BuildFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestCaseRunCreate(XmlrpcAPIBaseTest):
    """Test testcaserun.create"""

    def _fixture_setup(self):
        super(TestCaseRunCreate, self)._fixture_setup()

        self.staff = UserFactory(username='staff', email='staff@example.com')

        self.product = ProductFactory(name='Nitrate')
        self.version = VersionFactory(value='0.1', product=self.product)
        self.build = self.product.build.all()[0]
        self.plan = TestPlanFactory(author=self.api_user, owner=self.api_user, product=self.product)
        self.test_run = TestRunFactory(product_version=self.version, build=self.build,
                                       default_tester=None, plan=self.plan)
        self.case_run_status = TestCaseRunStatus.objects.get(name='IDLE')
        self.case = TestCaseFactory(author=self.api_user, default_tester=None, plan=[self.plan])

        self.case_run_pks = []

    def test_create_with_no_required_fields(self):
        values = [
            {
                "assignee": self.staff.pk,
                "case_run_status": self.case_run_status.pk,
                "notes": "unit test 2"
            },
            {
                "build": self.build.pk,
                "assignee": self.staff.pk,
                "case_run_status": 1,
                "notes": "unit test 2"
            },
            {
                "run": self.test_run.pk,
                "build": self.build.pk,
                "assignee": self.staff.pk,
                "case_run_status": self.case_run_status.pk,
                "notes": "unit test 2"
            },
        ]
        for value in values:
            with self.assertRaisesRegex(XmlRPCFault, 'This field is required'):
                self.rpc_client.TestCaseRun.create(value)

    def test_create_with_required_fields(self):
        tcr = self.rpc_client.TestCaseRun.create({
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "case_text_version": 15,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEqual(tcr['build_id'], self.build.pk)
        self.assertEqual(tcr['case_id'], self.case.pk)
        self.assertEqual(tcr['run_id'], self.test_run.pk)

    def test_create_with_all_fields(self):
        tcr = self.rpc_client.TestCaseRun.create({
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "assignee": self.api_user.pk,
            "notes": "test_create_with_all_fields",
            "sortkey": 90,
            "case_run_status": self.case_run_status.pk,
            "case_text_version": 3,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEqual(tcr['build_id'], self.build.pk)
        self.assertEqual(tcr['case_id'], self.case.pk)
        self.assertEqual(tcr['assignee_id'], self.api_user.pk)
        self.assertEqual(tcr['notes'], "test_create_with_all_fields")
        self.assertEqual(tcr['sortkey'], 90)
        self.assertEqual(tcr['case_run_status'], 'IDLE')
        self.assertEqual(tcr['case_text_version'], 3)

    def test_create_with_non_exist_fields(self):
        values = [
            {
                "run": self.test_run.pk,
                "build": self.build.pk,
                "case": 111111,
            },
            {
                "run": 11111,
                "build": self.build.pk,
                "case": self.case.pk,
            },
            {
                "run": self.test_run.pk,
                "build": 11222222,
                "case": self.case.pk,
            },
        ]
        for value in values:
            with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
                self.rpc_client.TestCaseRun.create(value)

    def test_create_with_chinese(self):
        tcr = self.rpc_client.TestCaseRun.create({
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "notes": u"开源中国",
            "case_text_version": 2,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEqual(tcr['build_id'], self.build.pk)
        self.assertEqual(tcr['case_id'], self.case.pk)
        self.assertEqual(tcr['assignee_id'], None)
        self.assertEqual(tcr['case_text_version'], 2)
        self.assertEqual(tcr['notes'], u"\u5f00\u6e90\u4e2d\u56fd")

    def test_create_with_long_field(self):
        large_str = """aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"""
        tcr = self.rpc_client.TestCaseRun.create({
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "notes": large_str,
            "case_text_version": 2,
        })
        self.assertIsNotNone(tcr)
        self.case_run_pks.append(tcr['case_run_id'])
        self.assertEqual(tcr['build_id'], self.build.pk)
        self.assertEqual(tcr['case_id'], self.case.pk)
        self.assertEqual(tcr['assignee_id'], None)
        self.assertEqual(tcr['case_text_version'], 2)
        self.assertEqual(tcr['notes'], large_str)

    def test_create_with_no_perm(self):
        values = {
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "assignee": self.api_user.pk,
            "notes": "test_create_with_all_fields",
            "sortkey": 2,
            "case_run_status": self.case_run_status.pk,
        }
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestCaseRun.create(values)


class TestCaseRunAddComment(XmlrpcAPIBaseTest):
    """Test testcaserun.add_comment"""

    def _fixture_setup(self):
        super(TestCaseRunAddComment, self)._fixture_setup()

        self.case_run_1 = TestCaseRunFactory()
        self.case_run_2 = TestCaseRunFactory()

    def test_add_comment_with_int(self):
        comment = self.rpc_client.TestCaseRun.add_comment(self.case_run_2.pk, "Hello World!")
        self.assertIsNone(comment)


class TestCaseRunAttachLog(XmlrpcAPIBaseTest):
    """Test testcaserun.add_log"""

    def _fixture_setup(self):
        super(TestCaseRunAttachLog, self)._fixture_setup()

        self.case_run = TestCaseRunFactory()

    def test_attach_log_with_non_existing_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'constraint fail|violates foreign key'):
            self.rpc_client.TestCaseRun.add_log(-5, 'A test log', 'http://example.com')

    def test_attach_log_with_invalid_url(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Enter a valid URL'):
            self.rpc_client.TestCaseRun.add_log(self.case_run.pk, "UT test logs", 'aaaaaaaaa')

    def test_attach_log(self):
        url = "http://127.0.0.1/test/test-log.log"
        log_id = self.rpc_client.TestCaseRun.add_log(self.case_run.pk, "UT test logs", url)
        self.assertGreater(log_id, 0)


class TestCaseRunDetachLog(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCaseRunDetachLog, self)._fixture_setup()

        self.status_idle = TestCaseRunStatus.objects.get(name='IDLE')
        self.tester = UserFactory()
        self.case_run = TestCaseRunFactory(assignee=self.tester, tested_by=None,
                                           notes='testing ...',
                                           sortkey=10,
                                           case_run_status=self.status_idle)

    def setUp(self):
        super(TestCaseRunDetachLog, self).setUp()

        self.rpc_client.TestCaseRun.add_log(
            self.case_run.pk, 'Related issue', 'https://localhost/issue/1')
        self.link = self.case_run.links()[0]

    def test_doesnt_raise_with_non_existing_id(self):
        self.rpc_client.TestCaseRun.remove_log(-9, self.link.pk)
        links = self.case_run.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log_with_non_exist_log(self):
        self.rpc_client.TestCaseRun.remove_log(self.case_run.pk, 999999999)
        links = self.case_run.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log(self):
        self.rpc_client.TestCaseRun.remove_log(self.case_run.pk, self.link.pk)
        self.assertEqual([], list(self.case_run.links()))


class TestCaseRunFilter(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCaseRunFilter, self)._fixture_setup()

        self.status_idle = TestCaseRunStatus.objects.get(name='IDLE')
        self.tester = UserFactory()
        self.case_run = TestCaseRunFactory(assignee=self.tester, tested_by=None,
                                           notes='testing ...',
                                           sortkey=10,
                                           case_run_status=self.status_idle)

    def test_with_non_exist_id(self):
        found = self.rpc_client.TestCaseRun.filter({'pk': -1})
        self.assertEqual(0, len(found))

    def test_filter_by_id(self):
        tcr = self.rpc_client.TestCaseRun.filter({'pk': self.case_run.pk})[0]
        self.assertIsNotNone(tcr)
        self.assertEqual(tcr['build_id'], self.case_run.build.pk)
        self.assertEqual(tcr['case_id'], self.case_run.case.pk)
        self.assertEqual(tcr['assignee_id'], self.tester.pk)
        self.assertEqual(tcr['tested_by_id'], None)
        self.assertEqual(tcr['notes'], 'testing ...')
        self.assertEqual(tcr['sortkey'], 10)
        self.assertEqual(tcr['case_run_status'], 'IDLE')
        self.assertEqual(tcr['case_run_status_id'], self.status_idle.pk)


class TestCaseRunGetLogs(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCaseRunGetLogs, self)._fixture_setup()

        self.case_run_1 = TestCaseRunFactory()
        self.case_run_2 = TestCaseRunFactory()

        self.rpc_client.TestCaseRun.add_log(
            self.case_run_1.pk,
            "Test logs",
            "http://www.google.com")

    def test_get_logs_with_non_exist_id(self):
        result = self.rpc_client.TestCaseRun.get_logs(-9)
        self.assertEqual([], result)

    def test_get_empty_logs(self):
        logs = self.rpc_client.TestCaseRun.get_logs(self.case_run_2.pk)
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 0)

    def test_get_logs(self):
        tcr_log = LinkReference.objects.get(test_case_run=self.case_run_1.pk)
        logs = self.rpc_client.TestCaseRun.get_logs(self.case_run_1.pk)
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['id'], tcr_log.pk)
        self.assertEqual(logs[0]['name'], "Test logs")
        self.assertEqual(logs[0]['url'], "http://www.google.com")


class TestCaseRunUpdate(XmlrpcAPIBaseTest):

    def _fixture_setup(self):
        super(TestCaseRunUpdate, self)._fixture_setup()

        self.user = UserFactory()
        self.build = BuildFactory()
        self.case_run_1 = TestCaseRunFactory()
        self.case_run_2 = TestCaseRunFactory()
        self.status_running = TestCaseRunStatus.objects.get(name='RUNNING')

    def test_update_with_single_caserun(self):
        tcr = self.rpc_client.TestCaseRun.update(self.case_run_1.pk, {
            "build": self.build.pk,
            "assignee": self.user.pk,
            "case_run_status": self.status_running.pk,
            "notes": "AAAAAAAA",
            "sortkey": 90
        })
        self.assertEqual(tcr['build'], self.build.name)
        self.assertEqual(tcr['assignee'], self.user.username)
        self.assertEqual(tcr['case_run_status'], 'RUNNING')
        self.assertEqual(tcr['notes'], "AAAAAAAA")
        self.assertEqual(tcr['sortkey'], 90)

    def test_update_with_non_existing_build(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
            self.rpc_client.TestCaseRun.update(self.case_run_1.pk, {"build": 1111111})

    def test_update_with_non_existing_assignee(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
            self.rpc_client.TestCaseRun.update(self.case_run_1.pk, {"assignee": 1111111})

    def test_update_with_non_existing_status(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
            self.rpc_client.TestCaseRun.update(self.case_run_1.pk, {"case_run_status": 1111111})

    def test_update_by_ignoring_undocumented_fields(self):
        case_run = self.rpc_client.TestCaseRun.update(self.case_run_1.pk, {
            "notes": "AAAA",
            "close_date": datetime.now(),
            'anotherone': 'abc',
        })
        self.assertEqual('AAAA', case_run['notes'])

    def test_update_with_no_perm(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestCaseRun.update(self.case_run_1.pk, {"notes": "AAAA"})
