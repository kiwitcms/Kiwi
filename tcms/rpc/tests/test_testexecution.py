# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault
from xmlrpc.client import ProtocolError

from django.test import override_settings
from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers.comments import get_comments
from tcms.rpc.tests.utils import APITestCase
from tcms.testruns.models import TestExecutionStatus
from tcms.tests.factories import (BuildFactory,
                                  TestCaseFactory, TestExecutionFactory,
                                  TestPlanFactory, TestRunFactory, UserFactory,
                                  VersionFactory)


@override_settings(LANGUAGE_CODE='en')
class TestExecutionCreate(APITestCase):  # pylint: disable=too-many-instance-attributes
    """Test TestExecution.create"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.staff = UserFactory()

        self.version = VersionFactory()
        self.build = self.version.product.build.first()
        self.plan = TestPlanFactory(author=self.api_user, product=self.version.product)
        self.test_run = TestRunFactory(product_version=self.version, build=self.build,
                                       default_tester=None, plan=self.plan)
        self.status = TestExecutionStatus.objects.filter(weight=0).first()
        self.case = TestCaseFactory(author=self.api_user, default_tester=None, plan=[self.plan])

    def test_create_with_no_required_fields(self):
        values = [
            {
                "assignee": self.staff.pk,
                "status": self.status.pk,
            },
            {
                "build": self.build.pk,
                "assignee": self.staff.pk,
                "status": 1,
            },
            {
                "run": self.test_run.pk,
                "build": self.build.pk,
                "assignee": self.staff.pk,
                "status": self.status.pk,
            },
        ]
        for value in values:
            with self.assertRaisesRegex(XmlRPCFault, 'This field is required'):
                self.rpc_client.TestExecution.create(value)

    def test_create_with_required_fields(self):
        execution = self.rpc_client.TestExecution.create({
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "case_text_version": 15,
        })
        self.assertIsNotNone(execution)
        self.assertIsNotNone(execution['id'])
        self.assertEqual(execution['build_id'], self.build.pk)
        self.assertEqual(execution['case_id'], self.case.pk)
        self.assertEqual(execution['run_id'], self.test_run.pk)

    def test_create_with_all_fields(self):
        execution = self.rpc_client.TestExecution.create({
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "assignee": self.api_user.pk,
            "sortkey": 90,
            "status": self.status.pk,
            "case_text_version": 3,
        })
        self.assertIsNotNone(execution)
        self.assertIsNotNone(execution['id'])
        self.assertEqual(execution['build_id'], self.build.pk)
        self.assertEqual(execution['case_id'], self.case.pk)
        self.assertEqual(execution['assignee_id'], self.api_user.pk)
        self.assertEqual(execution['sortkey'], 90)
        self.assertEqual(execution['status'], self.status.name)
        self.assertEqual(execution['case_text_version'], 3)

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
                self.rpc_client.TestExecution.create(value)

    def test_create_with_no_perm(self):
        values = {
            "run": self.test_run.pk,
            "build": self.build.pk,
            "case": self.case.pk,
            "assignee": self.api_user.pk,
            "sortkey": 2,
            "status": self.status.pk,
        }
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestExecution.create(values)


class TestExecutionAddComment(APITestCase):
    """Test TestExecution.add_comment"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_2 = TestExecutionFactory()

    def test_add_comment_with_pk_as_int(self):
        self.rpc_client.TestExecution.add_comment(self.execution_2.pk,
                                                  "Hello World!")
        comments = get_comments(self.execution_2)
        self.assertEqual(1, comments.count())

        first_comment = comments.first()
        self.assertEqual("Hello World!", first_comment.comment)


@override_settings(LANGUAGE_CODE='en')
class TestExecutionAddLink(APITestCase):
    """Test TestExecution.add_link"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.case_run = TestExecutionFactory()

    def test_attach_log_with_non_existing_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'constraint fail|violates foreign key'):
            self.rpc_client.TestExecution.add_link({
                'execution_id': -5,
                'name': 'A test log',
                'url': 'http://example.com'})

    def test_attach_log(self):
        url = "http://127.0.0.1/test/test-log.log"
        result = self.rpc_client.TestExecution.add_link({
            'execution_id': self.case_run.pk,
            'name': 'UT test logs',
            'url': url})
        self.assertGreater(result['id'], 0)
        self.assertEqual(result['url'], url)


class TestExecutionRemoveLink(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        self.tester = UserFactory()
        self.case_run = TestExecutionFactory(assignee=self.tester, tested_by=None,
                                             sortkey=10,
                                             status=self.status_idle)

    def setUp(self):
        super().setUp()

        self.rpc_client.TestExecution.add_link({
            'execution_id': self.case_run.pk,
            'name': 'Related issue',
            'url': 'https://localhost/issue/1'})
        self.link = self.case_run.links()[0]

    def test_doesnt_raise_with_non_existing_id(self):
        self.rpc_client.TestExecution.remove_link({'execution_id': -9})
        links = self.case_run.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log_with_non_exist_log(self):
        self.rpc_client.TestExecution.remove_link({'pk': 999999999})
        links = self.case_run.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log(self):
        self.rpc_client.TestExecution.remove_link({'execution_id': self.case_run.pk,
                                                   'pk': self.link.pk})
        self.assertEqual([], list(self.case_run.links()))


class TestExecutionFilter(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        self.tester = UserFactory()
        self.case_run = TestExecutionFactory(assignee=self.tester, tested_by=None,
                                             sortkey=10,
                                             status=self.status_idle)

    def test_with_non_exist_id(self):
        found = self.rpc_client.TestExecution.filter({'pk': -1})
        self.assertEqual(0, len(found))

    def test_filter_by_id(self):
        execution = self.rpc_client.TestExecution.filter({'pk': self.case_run.pk})[0]
        self.assertIsNotNone(execution)
        self.assertEqual(execution['build_id'], self.case_run.build.pk)
        self.assertEqual(execution['case_id'], self.case_run.case.pk)
        self.assertEqual(execution['assignee_id'], self.tester.pk)
        self.assertEqual(execution['tested_by_id'], None)
        self.assertEqual(execution['sortkey'], 10)
        self.assertEqual(execution['status'], self.status_idle.name)
        self.assertEqual(execution['status_id'], self.status_idle.pk)


class TestExecutionGetLinks(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.case_run_1 = TestExecutionFactory()
        self.case_run_2 = TestExecutionFactory()

        self.rpc_client.TestExecution.add_link({
            'execution_id': self.case_run_1.pk,
            'name': 'Test logs',
            'url': 'http://kiwitcms.org'})

    def test_get_links_with_non_exist_id(self):
        result = self.rpc_client.TestExecution.get_links({'execution': -9})
        self.assertEqual([], result)

    def test_get_empty_logs(self):
        logs = self.rpc_client.TestExecution.get_links({'execution': self.case_run_2.pk})
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 0)

    def test_get_links(self):
        execution_log = LinkReference.objects.get(execution=self.case_run_1.pk)
        logs = self.rpc_client.TestExecution.get_links({'execution': self.case_run_1.pk})
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['id'], execution_log.pk)
        self.assertEqual(logs[0]['name'], "Test logs")
        self.assertEqual(logs[0]['url'], 'http://kiwitcms.org')


@override_settings(LANGUAGE_CODE='en')
class TestExecutionUpdate(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.user = UserFactory()
        self.build = BuildFactory()
        self.case_run_1 = TestExecutionFactory()
        self.case_run_2 = TestExecutionFactory()
        self.status_positive = TestExecutionStatus.objects.filter(weight__gt=0).last()

    def test_update_with_single_caserun(self):
        execution = self.rpc_client.TestExecution.update(self.case_run_1.pk, {
            "build": self.build.pk,
            "assignee": self.user.pk,
            "status": self.status_positive.pk,
            "sortkey": 90
        })
        self.assertEqual(execution['build'], self.build.name)
        self.assertEqual(execution['assignee'], self.user.username)
        self.assertEqual(execution['status'], self.status_positive.name)
        self.assertEqual(execution['sortkey'], 90)

    def test_update_with_assignee_id(self):
        self.assertNotEqual(self.case_run_1.assignee, self.user.pk)
        execution = self.rpc_client.TestExecution.update(self.case_run_1.pk, {
            "assignee": self.user.pk
        })
        self.assertEqual(execution['assignee'], self.user.username)

    def test_update_with_assignee_email(self):
        self.assertNotEqual(self.case_run_1.assignee, self.user.email)
        execution = self.rpc_client.TestExecution.update(self.case_run_1.pk, {
            "assignee": self.user.email
        })
        self.assertEqual(execution['assignee'], self.user.username)

    def test_update_with_assignee_username(self):
        self.assertNotEqual(self.case_run_1.assignee, self.user.username)
        execution = self.rpc_client.TestExecution.update(self.case_run_1.pk, {
            "assignee": self.user.username
        })
        self.assertEqual(execution['assignee'], self.user.username)

    def test_update_with_non_existing_build(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
            self.rpc_client.TestExecution.update(self.case_run_1.pk, {"build": 1111111})

    def test_update_with_non_existing_assignee_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user_id'):
            self.rpc_client.TestExecution.update(self.case_run_1.pk, {
                "assignee": 1111111
            })

    def test_update_with_non_existing_assignee_email(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user'):
            self.rpc_client.TestExecution.update(self.case_run_1.pk, {
                "assignee": 'nonExistentEmail@gmail.com'
            })

    def test_update_with_non_existing_assignee_username(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user:'):
            self.rpc_client.TestExecution.update(self.case_run_1.pk, {
                "assignee": 'nonExistentUsername'
            })

    def test_update_when_case_text_version_is_integer(self):
        initial_case_text_version = self.case_run_1.case_text_version
        self.update_test_case_text()

        execution = self.rpc_client.TestExecution.update(self.case_run_1.pk, {
            "case_text_version": str(self.case_run_1.case.history.latest().history_id)
        })
        self.case_run_1.refresh_from_db()

        latest_case_text_version = self.case_run_1.case_text_version
        self.assertNotEqual(initial_case_text_version, latest_case_text_version)
        self.assertEqual(execution["case_text_version"], latest_case_text_version)
        self.assertEqual(self.case_run_1.case.history.latest().history_id, latest_case_text_version)

    def test_update_when_case_text_version_is_string_latest(self):
        initial_case_text_version = self.case_run_1.case_text_version
        self.update_test_case_text()

        execution = self.rpc_client.TestExecution.update(self.case_run_1.pk, {
            "case_text_version": 'latest'
        })
        self.case_run_1.refresh_from_db()

        latest_case_text_version = self.case_run_1.case_text_version
        self.assertNotEqual(initial_case_text_version, latest_case_text_version)
        self.assertEqual(execution["case_text_version"], latest_case_text_version)
        self.assertEqual(self.case_run_1.case.history.latest().history_id, latest_case_text_version)

    def update_test_case_text(self):
        self.case_run_1.case.summary = "Summary Updated"
        self.case_run_1.case.text = "Text Updated"
        self.case_run_1.case.save()

    def test_update_with_non_existing_status(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
            self.rpc_client.TestExecution.update(self.case_run_1.pk,
                                                 {"status": 1111111})

    def test_update_with_no_perm(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestExecution.update(self.case_run_1.pk,
                                                 {"close_date": timezone.now()})
