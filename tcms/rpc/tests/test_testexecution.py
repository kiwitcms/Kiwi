# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault
from xmlrpc.client import ProtocolError

from django.test import override_settings
from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers.comments import get_comments
from tcms.rpc.tests.utils import APITestCase, APIPermissionsTestCase
from tcms.testruns.models import TestExecutionStatus
from tcms.tests.factories import BuildFactory
from tcms.tests.factories import LinkReferenceFactory
from tcms.tests.factories import TestExecutionFactory
from tcms.tests.factories import UserFactory


class TestExecutionAddComment(APITestCase):
    """Test TestExecution.add_comment"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_2 = TestExecutionFactory()

    def test_add_comment_with_pk_as_int(self):
        created_comment = self.rpc_client.TestExecution.add_comment(self.execution_2.pk,
                                                                    "Hello World!")
        comments = get_comments(self.execution_2)
        self.assertEqual(1, comments.count())

        first_comment = comments.first()
        self.assertEqual("Hello World!", first_comment.comment)
        self.assertEqual(created_comment['comment'], first_comment.comment)


@override_settings(LANGUAGE_CODE='en')
class TestExecutionAddLink(APITestCase):
    """Test TestExecution.add_link"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()

    def test_attach_log_with_non_existing_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'constraint fail|violates foreign key'):
            self.rpc_client.TestExecution.add_link({
                'execution_id': -5,
                'name': 'A test log',
                'url': 'http://example.com'})

    def test_attach_log(self):
        url = "http://127.0.0.1/test/test-log.log"
        result = self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution.pk,
            'name': 'UT test logs',
            'url': url})
        self.assertGreater(result['id'], 0)
        self.assertEqual(result['url'], url)


class TestExecutionAddLinkPermissions(APIPermissionsTestCase):
    """Test permissions of TestExecution.add_link"""

    permission_label = 'linkreference.add_linkreference'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        links = self.execution.links()
        self.assertFalse(links.exists())

        url = 'http://example.com'
        result = self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution.pk,
            'url': url})

        links = self.execution.links()
        self.assertEqual(self.execution.pk, result['execution'])
        self.assertEqual(url, result['url'])
        self.assertEqual(1, links.count())
        self.assertEqual(url, links.first().url)

    def verify_api_without_permission(self):
        url = 'http://127.0.0.1/test/test-log.log'
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestExecution.add_link({
                'execution_id': self.execution.pk,
                'name': 'UT test logs',
                'url': url})


class TestExecutionRemoveLink(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        self.tester = UserFactory()
        self.execution = TestExecutionFactory(assignee=self.tester, tested_by=None,
                                              sortkey=10,
                                              status=self.status_idle)

    def setUp(self):
        super().setUp()

        self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution.pk,
            'name': 'Related issue',
            'url': 'https://localhost/issue/1'})
        self.link = self.execution.links()[0]

    def test_doesnt_raise_with_non_existing_id(self):
        self.rpc_client.TestExecution.remove_link({'execution_id': -9})
        links = self.execution.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log_with_non_exist_log(self):
        self.rpc_client.TestExecution.remove_link({'pk': 999999999})
        links = self.execution.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log(self):
        self.rpc_client.TestExecution.remove_link({'execution_id': self.execution.pk,
                                                   'pk': self.link.pk})
        self.assertEqual([], list(self.execution.links()))


class TestExecutionRemoveLinkPermissions(APIPermissionsTestCase):
    """Test permissions of TestExecution.remove_link"""

    permission_label = 'linkreference.delete_linkreference'

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()
        self.link = LinkReferenceFactory(execution=self.execution)
        self.another_link = LinkReferenceFactory(execution=self.execution)

    def verify_api_with_permission(self):
        links = self.execution.links()
        self.assertEqual(2, links.count())
        self.assertIn(self.link, links)
        self.assertIn(self.another_link, links)

        self.rpc_client.TestExecution.remove_link({'pk': self.link.pk})

        links = self.execution.links()
        self.assertEqual(1, links.count())
        self.assertIn(self.another_link, links)
        self.assertNotIn(self.link, links)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestExecution.remove_link({'pk': self.another_link.pk})


class TestExecutionFilter(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        self.tester = UserFactory()
        self.execution = TestExecutionFactory(assignee=self.tester, tested_by=None,
                                              sortkey=10,
                                              status=self.status_idle)

    def test_with_non_exist_id(self):
        found = self.rpc_client.TestExecution.filter({'pk': -1})
        self.assertEqual(0, len(found))

    def test_filter_by_id(self):
        execution = self.rpc_client.TestExecution.filter({'pk': self.execution.pk})[0]
        self.assertIsNotNone(execution)
        self.assertEqual(execution['build_id'], self.execution.build.pk)
        self.assertEqual(execution['case_id'], self.execution.case.pk)
        self.assertEqual(execution['assignee_id'], self.tester.pk)
        self.assertEqual(execution['tested_by_id'], None)
        self.assertEqual(execution['sortkey'], 10)
        self.assertEqual(execution['status'], self.status_idle.name)
        self.assertEqual(execution['status_id'], self.status_idle.pk)


class TestExecutionGetLinks(APITestCase):

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_2 = TestExecutionFactory()

        self.rpc_client.TestExecution.add_link({
            'execution_id': self.execution_1.pk,
            'name': 'Test logs',
            'url': 'http://kiwitcms.org'})

    def test_get_links_with_non_exist_id(self):
        result = self.rpc_client.TestExecution.get_links({'execution': -9})
        self.assertEqual([], result)

    def test_get_empty_logs(self):
        logs = self.rpc_client.TestExecution.get_links({'execution': self.execution_2.pk})
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 0)

    def test_get_links(self):
        execution_log = LinkReference.objects.get(execution=self.execution_1.pk)
        logs = self.rpc_client.TestExecution.get_links({'execution': self.execution_1.pk})
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
        self.execution_1 = TestExecutionFactory()
        self.execution_2 = TestExecutionFactory()
        self.status_positive = TestExecutionStatus.objects.filter(weight__gt=0).last()

    def test_update_with_single_caserun(self):
        execution = TestExecutionFactory(tested_by=None)

        execution = self.rpc_client.TestExecution.update(execution.pk, {
            "build": self.build.pk,
            "assignee": self.user.pk,
            "sortkey": 90
        })
        self.assertEqual(execution['build'], self.build.name)
        self.assertEqual(execution['assignee'], self.user.username)
        self.assertEqual(execution['sortkey'], 90)
        self.assertIsNone(execution['tested_by'])

    def test_update_with_assignee_id(self):
        self.assertNotEqual(self.execution_1.assignee, self.user)
        execution = self.rpc_client.TestExecution.update(self.execution_1.pk, {
            "assignee": self.user.pk
        })
        self.execution_1.refresh_from_db()

        self.assertEqual(execution['assignee'], self.user.username)
        self.assertEqual(self.execution_1.assignee, self.user)

    def test_update_with_assignee_email(self):
        self.assertNotEqual(self.execution_1.assignee, self.user)
        execution = self.rpc_client.TestExecution.update(self.execution_1.pk, {
            "assignee": self.user.email
        })
        self.execution_1.refresh_from_db()

        self.assertEqual(execution['assignee'], self.user.username)
        self.assertEqual(self.execution_1.assignee, self.user)

    def test_update_with_assignee_username(self):
        self.assertNotEqual(self.execution_1.assignee, self.user)
        execution = self.rpc_client.TestExecution.update(self.execution_1.pk, {
            "assignee": self.user.username
        })
        self.execution_1.refresh_from_db()

        self.assertEqual(execution['assignee'], self.user.username)
        self.assertEqual(self.execution_1.assignee, self.user)

    def test_update_with_tested_by_id(self):
        self.assertNotEqual(self.execution_2.tested_by, self.user)
        execution = self.rpc_client.TestExecution.update(self.execution_2.pk, {
            "tested_by": self.user.pk
        })
        self.execution_2.refresh_from_db()

        self.assertEqual(execution['tested_by'], self.user.username)
        self.assertEqual(self.execution_2.tested_by, self.user)

    def test_update_with_tested_by_email(self):
        self.assertNotEqual(self.execution_2.tested_by, self.user)
        execution = self.rpc_client.TestExecution.update(self.execution_2.pk, {
            "tested_by": self.user.email
        })
        self.execution_2.refresh_from_db()

        self.assertEqual(execution['tested_by'], self.user.username)
        self.assertEqual(self.execution_2.tested_by, self.user)

    def test_update_with_tested_by_username(self):
        self.assertNotEqual(self.execution_2.tested_by, self.user)
        execution = self.rpc_client.TestExecution.update(self.execution_2.pk, {
            "tested_by": self.user.username
        })
        self.execution_2.refresh_from_db()

        self.assertEqual(execution['tested_by'], self.user.username)
        self.assertEqual(self.execution_2.tested_by, self.user)

    def test_update_with_non_existing_build(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
            self.rpc_client.TestExecution.update(self.execution_1.pk, {"build": 1111111})

    def test_update_with_non_existing_assignee_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user_id'):
            self.rpc_client.TestExecution.update(self.execution_1.pk, {
                "assignee": 1111111
            })

    def test_update_with_non_existing_assignee_email(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user'):
            self.rpc_client.TestExecution.update(self.execution_1.pk, {
                "assignee": 'nonExistentEmail@gmail.com'
            })

    def test_update_with_non_existing_assignee_username(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user'):
            self.rpc_client.TestExecution.update(self.execution_1.pk, {
                "assignee": 'nonExistentUsername'
            })

    def test_update_with_non_existing_tested_by_id(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user_id'):
            self.rpc_client.TestExecution.update(self.execution_2.pk, {
                "tested_by": 1111111
            })

    def test_update_with_non_existing_tested_by_email(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user'):
            self.rpc_client.TestExecution.update(self.execution_2.pk, {
                "tested_by": 'nonExistentEmail@gmail.com'
            })

    def test_update_with_non_existing_tested_by_username(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user:'):
            self.rpc_client.TestExecution.update(self.execution_2.pk, {
                "tested_by": 'nonExistentUsername'
            })

    def test_update_when_case_text_version_is_integer(self):
        initial_case_text_version = self.execution_1.case_text_version
        self.update_test_case_text()

        execution = self.rpc_client.TestExecution.update(self.execution_1.pk, {
            "case_text_version": str(self.execution_1.case.history.latest().history_id)
        })
        self.execution_1.refresh_from_db()

        latest_case_text_version = self.execution_1.case_text_version
        self.assertNotEqual(initial_case_text_version, latest_case_text_version)
        self.assertEqual(execution["case_text_version"], latest_case_text_version)
        self.assertEqual(self.execution_1.case.history.latest().history_id,
                         latest_case_text_version)

    def test_update_when_case_text_version_is_string_latest(self):
        initial_case_text_version = self.execution_1.case_text_version
        self.update_test_case_text()

        execution = self.rpc_client.TestExecution.update(self.execution_1.pk, {
            "case_text_version": 'latest'
        })
        self.execution_1.refresh_from_db()

        latest_case_text_version = self.execution_1.case_text_version
        self.assertNotEqual(initial_case_text_version, latest_case_text_version)
        self.assertEqual(execution["case_text_version"], latest_case_text_version)
        self.assertEqual(self.execution_1.case.history.latest().history_id,
                         latest_case_text_version)

    def update_test_case_text(self):
        self.execution_1.case.summary = "Summary Updated"
        self.execution_1.case.text = "Text Updated"
        self.execution_1.case.save()

    def test_update_with_status_changes_tested_by(self):
        execution = TestExecutionFactory(
            tested_by=self.user
        )

        self.rpc_client.TestExecution.update(execution.pk, {"status": self.status_positive.pk})
        execution.refresh_from_db()

        self.assertEqual(execution.tested_by, self.api_user)
        self.assertEqual(execution.status, self.status_positive)

    def test_update_with_non_existing_status(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Select a valid choice'):
            self.rpc_client.TestExecution.update(self.execution_1.pk,
                                                 {"status": 1111111})

    def test_update_with_no_perm(self):
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(ProtocolError, '403 Forbidden'):
            self.rpc_client.TestExecution.update(self.execution_1.pk,
                                                 {"close_date": timezone.now()})
