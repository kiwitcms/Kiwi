# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init, objects-update-used, too-many-lines

import time
from datetime import datetime, timedelta

from attachments.models import Attachment
from django.forms.models import model_to_dict
from django.test import override_settings
from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers import comments
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testruns.models import TestExecution, TestExecutionStatus
from tcms.tests import remove_perm_from_user, user_should_have_perm
from tcms.tests.factories import (
    BuildFactory,
    LinkReferenceFactory,
    TestCaseFactory,
    TestExecutionFactory,
    TestRunFactory,
    UserFactory,
)
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestExecutionGetComments(APITestCase):
    """Test TestExecution.get_comments"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.comments = ["Text for first comment", "Text for second comment"]

        cls.execution = TestExecutionFactory()
        for comment in cls.comments:
            comments.add_comment([cls.execution], comment, cls.api_user)

    def test_get_comments(self):
        execution_comments = self.rpc_client.TestExecution.get_comments(
            self.execution.pk
        )

        self.assertEqual(len(self.comments), len(execution_comments))
        for comment in execution_comments:
            self.assertIn(comment["comment"], self.comments)

    def test_get_comments_non_existing_execution(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestExecution matching query does not exist."
        ):
            self.rpc_client.TestExecution.get_comments(-1)


class TestExecutionGetCommentsPermissions(APIPermissionsTestCase):
    """Test permissions of TestExecution.get_comments"""

    permission_label = "django_comments.view_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()
        cls.comments = ["Text for first comment", "Text for second comment"]

        for comment in cls.comments:
            comments.add_comment([cls.execution], comment, cls.tester)

    def verify_api_with_permission(self):
        execution_comments = self.rpc_client.TestExecution.get_comments(
            self.execution.pk
        )

        self.assertEqual(len(self.comments), len(execution_comments))
        for comment in execution_comments:
            self.assertIn(comment["comment"], self.comments)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.get_comments"',
        ):
            self.rpc_client.TestExecution.get_comments(self.execution.pk)


class TestAddCommentFromRegularUser(APIPermissionsTestCase):
    permission_label = "django_comments.add_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution_1 = TestExecutionFactory()
        cls.execution_2 = TestExecutionFactory()

    def verify_api_with_permission(self):
        created_comment = self.rpc_client.TestExecution.add_comment(
            self.execution_2.pk, "Hello World!"
        )
        execution_comments = comments.get_comments(self.execution_2)
        self.assertEqual(1, execution_comments.count())
        self.assertEqual(created_comment["user"], self.tester.pk)
        self.assertGreater(
            created_comment["submit_date"], timezone.now() - timedelta(seconds=5)
        )
        self.assertLess(
            created_comment["submit_date"], timezone.now() + timedelta(seconds=1)
        )

        first_comment = execution_comments.first()
        self.assertEqual("Hello World!", first_comment.comment)
        self.assertEqual(created_comment["comment"], first_comment.comment)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.add_comment"',
        ):
            self.rpc_client.TestExecution.add_comment(
                self.execution_1.pk, "Hello World!"
            )


class TestAddCommentFromSuperUser(TestAddCommentFromRegularUser):
    def verify_api_with_permission(self):
        self.tester.is_superuser = True
        self.tester.save()

        new_user = UserFactory()

        # try overriding comment author
        result = self.rpc_client.TestExecution.add_comment(
            self.execution_1.pk, "Hello World", new_user.pk
        )

        self.assertEqual(result["comment"], "Hello World")
        self.assertEqual(result["is_public"], True)
        self.assertEqual(result["object_pk"], self.execution_1.pk)
        self.assertEqual(result["user"], new_user.pk)
        self.assertGreater(result["submit_date"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["submit_date"], timezone.now() + timedelta(seconds=1))

        # try overriding comment submit_date
        result = self.rpc_client.TestExecution.add_comment(
            self.execution_2.pk,
            "Happy Testing",
            new_user.pk,
            datetime(2026, 1, 4, 0, 0, 0),
        )

        self.assertEqual(result["comment"], "Happy Testing")
        self.assertEqual(result["object_pk"], self.execution_2.pk)
        self.assertEqual(result["user"], new_user.pk)
        self.assertEqual(result["submit_date"], datetime(2026, 1, 4, 0, 0, 0))


class TestExecutionRemoveComment(APITestCase):
    """Test TestExecution.remove_comment"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.user = UserFactory()
        cls.execution = TestExecutionFactory()

    def test_delete_all_comments(self):
        comments.add_comment([self.execution], "Hello World!", self.user)
        comments.add_comment([self.execution], "More comments", self.user)
        self.rpc_client.TestExecution.remove_comment(self.execution.pk)

        result = comments.get_comments(self.execution)
        self.assertEqual(result.count(), 0)

    def test_delete_one_comment(self):
        comments.add_comment([self.execution], "Hello World!", self.user)
        comment_2 = comments.add_comment([self.execution], "More comments", self.user)
        comment_2 = model_to_dict(comment_2[0])

        self.rpc_client.TestExecution.remove_comment(self.execution.pk, comment_2["id"])
        result = comments.get_comments(self.execution)
        first_comment = result.first()

        self.assertEqual(result.count(), 1)
        self.assertEqual("Hello World!", first_comment.comment)


class TestExecutionRemoveCommentPermissions(APIPermissionsTestCase):
    """Test TestExecution.remove_comment permissions"""

    permission_label = "django_comments.delete_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.user = UserFactory()
        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        comments.add_comment([self.execution], "Hello World!", self.user)
        self.rpc_client.TestExecution.remove_comment(self.execution.pk)

        result = comments.get_comments(self.execution)
        self.assertEqual(result.count(), 0)

    def verify_api_without_permission(self):
        comments.add_comment([self.execution], "Hello World!", self.user)

        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.remove_comment"',
        ):
            self.rpc_client.TestExecution.remove_comment(self.execution.pk)


@override_settings(LANGUAGE_CODE="en")
class TestExecutionAddLink(APITestCase):
    """Test TestExecution.add_link"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()

    def test_attach_log_with_non_existing_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, ".*execution.*Select a valid choice.*"
        ):
            self.rpc_client.TestExecution.add_link(
                {"execution_id": -5, "name": "A test log", "url": "http://example.com"}
            )

    def test_attach_log(self):
        url = "http://127.0.0.1/test/test-log.log"
        result = self.rpc_client.TestExecution.add_link(
            {"execution_id": self.execution.pk, "name": "UT test logs", "url": url}
        )
        self.assertGreater(result["id"], 0)
        self.assertEqual(result["url"], url)

    def test_add_link_with_name_longer_than_64_should_fail(self):
        with self.assertRaisesRegex(XmlRPCFault, "has at most 64 characters"):
            name = "a" * 65
            url = "http://127.0.0.1/test/test-log.log"
            self.rpc_client.TestExecution.add_link(
                {"execution_id": self.execution.pk, "name": name, "url": url}
            )


class TestExecutionAddLinkPermissions(APIPermissionsTestCase):
    """Test permissions of TestExecution.add_link"""

    permission_label = "linkreference.add_linkreference"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        links = self.execution.links()
        self.assertFalse(links.exists())

        url = "http://example.com"
        result = self.rpc_client.TestExecution.add_link(
            {"execution_id": self.execution.pk, "url": url}
        )

        links = self.execution.links()
        self.assertEqual(self.execution.pk, result["execution"])
        self.assertEqual(url, result["url"])
        self.assertEqual(1, links.count())
        self.assertEqual(url, links.first().url)

    def verify_api_without_permission(self):
        url = "http://127.0.0.1/test/test-log.log"
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestExecution.add_link"'
        ):
            self.rpc_client.TestExecution.add_link(
                {"execution_id": self.execution.pk, "name": "UT test logs", "url": url}
            )


class TestExecutionRemoveLink(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        cls.tester = UserFactory()
        cls.execution = TestExecutionFactory(
            assignee=cls.tester, tested_by=None, sortkey=10, status=cls.status_idle
        )

    def setUp(self):
        super().setUp()

        self.rpc_client.TestExecution.add_link(
            {
                "execution_id": self.execution.pk,
                "name": "Related issue",
                "url": "https://localhost/issue/1",
            }
        )
        self.link = self.execution.links()[0]

    def test_doesnt_raise_with_non_existing_id(self):
        self.rpc_client.TestExecution.remove_link({"execution_id": -9})
        links = self.execution.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log_with_non_exist_log(self):
        self.rpc_client.TestExecution.remove_link({"pk": 999999999})
        links = self.execution.links()
        self.assertEqual(1, links.count())
        self.assertEqual(self.link.pk, links[0].pk)

    def test_detach_log(self):
        self.rpc_client.TestExecution.remove_link(
            {"execution_id": self.execution.pk, "pk": self.link.pk}
        )
        self.assertEqual([], list(self.execution.links()))


class TestExecutionRemoveLinkPermissions(APIPermissionsTestCase):
    """Test permissions of TestExecution.remove_link"""

    permission_label = "linkreference.delete_linkreference"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()
        cls.link = LinkReferenceFactory(execution=cls.execution)
        cls.another_link = LinkReferenceFactory(execution=cls.execution)

    def verify_api_with_permission(self):
        links = self.execution.links()
        self.assertEqual(2, links.count())
        self.assertIn(self.link, links)
        self.assertIn(self.another_link, links)

        self.rpc_client.TestExecution.remove_link({"pk": self.link.pk})

        links = self.execution.links()
        self.assertEqual(1, links.count())
        self.assertIn(self.another_link, links)
        self.assertNotIn(self.link, links)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.remove_link"',
        ):
            self.rpc_client.TestExecution.remove_link({"pk": self.another_link.pk})


class TestExecutionFilter(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        cls.tester = UserFactory()
        cls.execution = TestExecutionFactory(
            assignee=cls.tester, tested_by=None, sortkey=10, status=cls.status_idle
        )

    def test_with_non_exist_id(self):
        found = self.rpc_client.TestExecution.filter({"pk": -1})
        self.assertEqual(0, len(found))

    def test_filter_by_id(self):
        execution = self.rpc_client.TestExecution.filter({"pk": self.execution.pk})[0]

        self.assertIsNotNone(execution)
        self.assertEqual(execution["id"], self.execution.pk)
        self.assertEqual(execution["assignee"], self.tester.pk)
        self.assertEqual(execution["tested_by"], None)
        self.assertEqual(
            execution["case_text_version"], self.execution.case_text_version
        )
        self.assertEqual(execution["start_date"], self.execution.start_date)
        self.assertEqual(execution["stop_date"], self.execution.stop_date)
        self.assertEqual(execution["sortkey"], self.execution.sortkey)
        self.assertEqual(execution["run"], self.execution.run.pk)
        self.assertEqual(execution["case"], self.execution.case.pk)
        self.assertEqual(execution["build"], self.execution.build.pk)
        self.assertEqual(execution["status"], self.status_idle.pk)
        self.assertIn("expected_duration", execution)


class ActualDurationProperty(APITestCase):
    def test_calculation_of_actual_duration(self):
        execution = TestExecutionFactory(
            start_date=timezone.now(),
            stop_date=timezone.now() + timezone.timedelta(days=1),
        )

        result = self.rpc_client.TestExecution.filter({"pk": execution.pk})[0]

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], execution.pk)
        self.assertEqual(
            result["actual_duration"], execution.actual_duration.total_seconds()
        )

    def test_actual_duration_empty_start_date(self):
        execution = TestExecutionFactory(
            start_date=None,
        )

        result = self.rpc_client.TestExecution.filter({"pk": execution.pk})[0]

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], execution.pk)
        self.assertIsNone(result["actual_duration"])

    def test_actual_duration_empty_stop_date(self):
        execution = TestExecutionFactory(
            start_date=timezone.now(),
        )

        result = self.rpc_client.TestExecution.filter({"pk": execution.pk})[0]

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], execution.pk)
        self.assertIsNone(result["actual_duration"])


class TestExecutionGetLinks(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution_1 = TestExecutionFactory()
        cls.execution_2 = TestExecutionFactory()

    def setUp(self):
        super().setUp()

        self.rpc_client.TestExecution.add_link(
            {
                "execution_id": self.execution_1.pk,
                "name": "Test logs",
                "url": "http://kiwitcms.org",
            }
        )

    def test_get_links_with_non_exist_id(self):
        result = self.rpc_client.TestExecution.get_links({"execution": -9})
        self.assertEqual([], result)

    def test_get_empty_logs(self):
        logs = self.rpc_client.TestExecution.get_links(
            {"execution": self.execution_2.pk}
        )
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 0)

    def test_get_links(self):
        execution_log = LinkReference.objects.get(execution=self.execution_1.pk)
        logs = self.rpc_client.TestExecution.get_links(
            {"execution": self.execution_1.pk}
        )
        self.assertIsInstance(logs, list)
        self.assertEqual(len(logs), 1)

        self.assertEqual(logs[0]["id"], execution_log.pk)
        self.assertEqual(logs[0]["name"], "Test logs")
        self.assertEqual(logs[0]["url"], "http://kiwitcms.org")
        self.assertEqual(logs[0]["execution"], self.execution_1.pk)
        self.assertIn("created_on", logs[0])
        self.assertFalse(logs[0]["is_defect"])


class TestExecutionHistory(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()

    def test_history_for_non_existing_execution(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestExecution matching query does not exist."
        ):
            self.rpc_client.TestExecution.history(-5)

    def test_history_new_execution(self):
        execution = TestExecutionFactory()

        history = self.rpc_client.TestExecution.history(execution.pk)

        self.assertEqual(1, len(history))

    def test_history(self):
        """
        Test that for an execution that has been updated 3 times,
        there are 4 history entries (first one is the creation of the object).

        Note: the `time.sleep` call after every update is necessary,
        because otherwise the changes happen too fast,
        and the XML-RPC protocol follows ISO 8601 which doesn't have sub-seconds precision.
        Hence the measurable delta is 1 second.
        """
        time.sleep(1)

        self.execution.build = BuildFactory()
        self.execution.save()
        time.sleep(1)

        user = UserFactory()
        self.execution.assignee = user
        self.execution.save()
        time.sleep(1)

        self.execution.tested_by = user
        self.execution.save()
        time.sleep(1)

        history = self.rpc_client.TestExecution.history(self.execution.pk)
        self.assertEqual(4, len(history))

        # assert entries are in the right order
        previous = timezone.now()
        for history_entry in history:
            self.assertLess(history_entry["history_date"], previous)
            previous = history_entry["history_date"]


class TestExecutionHistoryPermissions(APIPermissionsTestCase):
    """Test permissions of TestExecution.history"""

    permission_label = "testruns.view_historicaltestexecution"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        history = self.rpc_client.TestExecution.history(self.execution.pk)
        self.assertEqual(1, len(history))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestExecution.history"'
        ):
            self.rpc_client.TestExecution.history(self.execution.pk)


@override_settings(LANGUAGE_CODE="en")
class TestExecutionUpdate(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.user = UserFactory()
        cls.build = BuildFactory()
        cls.execution_1 = TestExecutionFactory()
        cls.execution_2 = TestExecutionFactory()
        cls.status_positive = TestExecutionStatus.objects.filter(weight__gt=0).last()

    def test_update_with_single_test_execution(self):
        execution = TestExecutionFactory(tested_by=None)

        result = self.rpc_client.TestExecution.update(
            execution.pk,
            {
                "build": self.build.pk,
                "assignee": self.user.pk,
                "sortkey": 90,
                "start_date": "2021-02-25",
                "stop_date": "2021-02-28 12:12:12",
            },
        )

        execution.refresh_from_db()

        self.assertEqual(result["id"], execution.pk)
        self.assertEqual(result["assignee"], self.user.pk)
        self.assertEqual(result["tested_by"], None)
        self.assertIn("case_text_version", result)
        self.assertEqual(result["start_date"], execution.start_date)
        self.assertEqual(result["stop_date"], execution.stop_date)
        self.assertEqual(result["sortkey"], 90)
        self.assertIn("run", result)
        self.assertIn("case", result)
        self.assertEqual(result["build"], self.build.pk)
        self.assertIn("status", result)

    def test_update_with_assignee_id(self):
        self.assertNotEqual(self.execution_1.assignee, self.user)
        execution = self.rpc_client.TestExecution.update(
            self.execution_1.pk, {"assignee": self.user.pk}
        )
        self.execution_1.refresh_from_db()

        self.assertEqual(execution["assignee"], self.user.pk)
        self.assertEqual(self.execution_1.assignee, self.user)

    def test_update_with_assignee_email(self):
        self.assertNotEqual(self.execution_1.assignee, self.user)
        execution = self.rpc_client.TestExecution.update(
            self.execution_1.pk, {"assignee": self.user.email}
        )
        self.execution_1.refresh_from_db()

        self.assertEqual(execution["assignee"], self.user.pk)
        self.assertEqual(self.execution_1.assignee, self.user)

    def test_update_with_assignee_username(self):
        self.assertNotEqual(self.execution_1.assignee, self.user)
        execution = self.rpc_client.TestExecution.update(
            self.execution_1.pk, {"assignee": self.user.username}
        )
        self.execution_1.refresh_from_db()

        self.assertEqual(execution["assignee"], self.user.pk)
        self.assertEqual(self.execution_1.assignee, self.user)

    def test_update_with_tested_by_id(self):
        self.assertNotEqual(self.execution_2.tested_by, self.user)
        execution = self.rpc_client.TestExecution.update(
            self.execution_2.pk, {"tested_by": self.user.pk}
        )
        self.execution_2.refresh_from_db()

        self.assertEqual(execution["tested_by"], self.user.pk)
        self.assertEqual(self.execution_2.tested_by, self.user)

    def test_update_with_tested_by_email(self):
        self.assertNotEqual(self.execution_2.tested_by, self.user)
        execution = self.rpc_client.TestExecution.update(
            self.execution_2.pk, {"tested_by": self.user.email}
        )
        self.execution_2.refresh_from_db()

        self.assertEqual(execution["tested_by"], self.user.pk)
        self.assertEqual(self.execution_2.tested_by, self.user)

    def test_update_with_tested_by_username(self):
        self.assertNotEqual(self.execution_2.tested_by, self.user)
        execution = self.rpc_client.TestExecution.update(
            self.execution_2.pk, {"tested_by": self.user.username}
        )
        self.execution_2.refresh_from_db()

        self.assertEqual(execution["tested_by"], self.user.pk)
        self.assertEqual(self.execution_2.tested_by, self.user)

    def test_update_with_non_existing_build(self):
        with self.assertRaisesRegex(XmlRPCFault, "Select a valid choice"):
            self.rpc_client.TestExecution.update(
                self.execution_1.pk, {"build": 1111111}
            )

    def test_update_with_non_existing_assignee_id(self):
        with self.assertRaisesRegex(XmlRPCFault, "Unknown user_id"):
            self.rpc_client.TestExecution.update(
                self.execution_1.pk, {"assignee": 1111111}
            )

    def test_update_with_non_existing_assignee_email(self):
        with self.assertRaisesRegex(XmlRPCFault, "Unknown user"):
            self.rpc_client.TestExecution.update(
                self.execution_1.pk, {"assignee": "nonExistentEmail@gmail.com"}
            )

    def test_update_with_non_existing_assignee_username(self):
        with self.assertRaisesRegex(XmlRPCFault, "Unknown user"):
            self.rpc_client.TestExecution.update(
                self.execution_1.pk, {"assignee": "nonExistentUsername"}
            )

    def test_update_with_non_existing_tested_by_id(self):
        with self.assertRaisesRegex(XmlRPCFault, "Unknown user_id"):
            self.rpc_client.TestExecution.update(
                self.execution_2.pk, {"tested_by": 1111111}
            )

    def test_update_with_non_existing_tested_by_email(self):
        with self.assertRaisesRegex(XmlRPCFault, "Unknown user"):
            self.rpc_client.TestExecution.update(
                self.execution_2.pk, {"tested_by": "nonExistentEmail@gmail.com"}
            )

    def test_update_with_non_existing_tested_by_username(self):
        with self.assertRaisesRegex(XmlRPCFault, "Unknown user:"):
            self.rpc_client.TestExecution.update(
                self.execution_2.pk, {"tested_by": "nonExistentUsername"}
            )

    def test_update_when_case_text_version_is_integer(self):
        initial_case_text_version = self.execution_1.case_text_version
        self.update_test_case_text()

        execution = self.rpc_client.TestExecution.update(
            self.execution_1.pk,
            {
                "case_text_version": str(
                    self.execution_1.case.history.latest().history_id
                )
            },
        )
        self.execution_1.refresh_from_db()

        latest_case_text_version = self.execution_1.case_text_version
        self.assertNotEqual(initial_case_text_version, latest_case_text_version)
        self.assertEqual(execution["case_text_version"], latest_case_text_version)
        self.assertEqual(
            self.execution_1.case.history.latest().history_id, latest_case_text_version
        )

    def test_update_when_case_text_version_is_string_latest(self):
        initial_case_text_version = self.execution_1.case_text_version
        self.update_test_case_text()

        execution = self.rpc_client.TestExecution.update(
            self.execution_1.pk, {"case_text_version": "latest"}
        )
        self.execution_1.refresh_from_db()

        latest_case_text_version = self.execution_1.case_text_version
        self.assertNotEqual(initial_case_text_version, latest_case_text_version)
        self.assertEqual(execution["case_text_version"], latest_case_text_version)
        self.assertEqual(
            self.execution_1.case.history.latest().history_id, latest_case_text_version
        )

    def update_test_case_text(self):
        self.execution_1.case.summary = "Summary Updated"
        self.execution_1.case.text = "Text Updated"
        self.execution_1.case.save()

    def test_update_with_no_perm(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestExecution.update"'
        ):
            # assign to a temp variable b/c self.rpc_client a property and calling it twice
            # in sequence results in 1st call logging out and 2nd call logging in automatically
            rpc_client = self.rpc_client

            rpc_client.Auth.logout()
            rpc_client.TestExecution.update(
                self.execution_1.pk, {"stop_date": timezone.now()}
            )


class TestExecutionUpdateStatus(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.user = UserFactory()
        cls.execution_1 = TestExecutionFactory()
        cls.status_positive = TestExecutionStatus.objects.filter(weight__gt=0).last()
        cls.status_negative = TestExecutionStatus.objects.filter(weight__lt=0).last()
        cls.status_in_progress = TestExecutionStatus.objects.filter(weight=0).last()

    def test_changes_tested_by(self):
        execution = TestExecutionFactory(tested_by=None)

        self.rpc_client.TestExecution.update(
            execution.pk, {"status": self.status_positive.pk}
        )
        execution.refresh_from_db()

        self.assertEqual(execution.tested_by, self.api_user)
        self.assertEqual(execution.status, self.status_positive)

    def test_when_tested_by_specified_does_not_change_tested_by(self):
        execution = TestExecutionFactory(tested_by=None)

        self.rpc_client.TestExecution.update(
            execution.pk,
            {
                "status": self.status_positive.pk,
                "tested_by": self.user.pk,
            },
        )
        execution.refresh_from_db()

        self.assertEqual(execution.tested_by, self.user)
        self.assertEqual(execution.status, self.status_positive)

    def test_changes_build(self):
        # simulate what happens in reality where TestExeuctions are created
        # taking their initial .build values from the parent TestRun
        self.execution_1.build = self.execution_1.run.build
        self.execution_1.save()

        # now simulate a re-test scenario where TR.build has already changed
        # e.g. longer test cycle covering multiple builds
        self.execution_1.run.build = BuildFactory(name="b02")
        self.execution_1.run.save()

        self.rpc_client.TestExecution.update(
            self.execution_1.pk, {"status": self.status_positive.pk}
        )

        self.execution_1.refresh_from_db()
        self.assertEqual(self.execution_1.status, self.status_positive)
        self.assertEqual(self.execution_1.build.name, "b02")

    def test_when_build_specified_does_not_change_build(self):
        # simulate what happens in reality where TestExeuctions are created
        # taking their initial .build values from the parent TestRun
        self.execution_1.build = self.execution_1.run.build
        self.execution_1.save()

        build03 = BuildFactory(name="b03")

        self.rpc_client.TestExecution.update(
            self.execution_1.pk,
            {
                "status": self.status_positive.pk,
                "build": build03.pk,
            },
        )

        self.execution_1.refresh_from_db()
        self.assertEqual(self.execution_1.status, self.status_positive)
        self.assertEqual(self.execution_1.build.name, "b03")
        # these are different b/c the API call (e.g. from a plugin) has
        # passed an explicit build value
        self.assertNotEqual(self.execution_1.run.build, build03)


class TestExecutionRemovePermissions(APIPermissionsTestCase):
    permission_label = "testruns.delete_testexecution"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.user = UserFactory()
        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        self.rpc_client.TestExecution.remove({"pk": self.execution.pk})

        exists = TestExecution.objects.filter(pk=self.execution.pk).exists()
        self.assertFalse(exists)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.remove"',
        ):
            self.rpc_client.TestExecution.remove({"pk": self.execution.pk})

            exists = TestExecution.objects.filter(pk=self.execution.pk).exists()
            self.assertTrue(exists)


class TestListAttachmentsPermissions(APIPermissionsTestCase):
    permission_label = "attachments.view_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        user_should_have_perm(self.tester, "attachments.add_attachment")
        self.rpc_client.TestExecution.add_attachment(
            self.execution.pk, "actual-results.txt", "a2l3aXRjbXM="
        )
        remove_perm_from_user(self.tester, "attachments.add_attachment")

        attachments = self.rpc_client.TestExecution.list_attachments(self.execution.pk)
        self.assertEqual(1, len(attachments))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.list_attachments"',
        ):
            self.rpc_client.TestExecution.list_attachments(self.execution.pk)


class TestListAttachmentsForUnknownId(TestListAttachmentsPermissions):
    def verify_api_with_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestExecution matching query does not exist"
        ):
            self.rpc_client.TestExecution.list_attachments(-1)


class TestAddAttachmentPermissions(APIPermissionsTestCase):
    permission_label = "attachments.add_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        self.rpc_client.TestExecution.add_attachment(
            self.execution.pk, "test-output.log", "a2l3aXRjbXM="
        )
        attachments = Attachment.objects.attachments_for_object(self.execution)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].object_id, str(self.execution.pk))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.add_attachment"',
        ):
            self.rpc_client.TestExecution.add_attachment(
                self.execution.pk, "test-output.txt", "a2l3aXRjbXM="
            )


class TestAddProperty(APIPermissionsTestCase):
    permission_label = "testruns.add_testexecutionproperty"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        result1 = self.rpc_client.TestExecution.add_property(
            self.execution.pk, "browser", "Firefox"
        )

        self.assertEqual(result1["execution"], self.execution.pk)
        self.assertEqual(result1["name"], "browser")
        self.assertEqual(result1["value"], "Firefox")

        # try adding again - should return existing value
        result2 = self.rpc_client.TestExecution.add_property(
            self.execution.pk, "browser", "Firefox"
        )
        self.assertEqual(result2["id"], result1["id"])
        self.assertEqual(result2["execution"], self.execution.pk)
        self.assertEqual(result2["name"], "browser")
        self.assertEqual(result2["value"], "Firefox")

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestExecution.add_property"',
        ):
            self.rpc_client.TestExecution.add_property(
                self.execution.pk, "browser", "Chrome"
            )


class TestCreate(APIPermissionsTestCase):
    permission_label = "testruns.add_testexecution"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()
        cls.test_case = TestCaseFactory()
        cls.new_user = UserFactory()

    def verify_api_with_permission(self):
        result = self.rpc_client.TestExecution.create(
            {
                "assignee": self.tester.pk,
                "tested_by": self.new_user.pk,
                "case_text_version": 123,
                "start_date": "2026-01-19 13:00:00",
                "stop_date": "2026-01-19 13:10:00",
                "sortkey": 10,
                "run": self.test_run.pk,
                "build": self.test_run.build.pk,
                "case": self.test_case.pk,
                "status": TestExecutionStatus.objects.first().pk,
            }
        )

        self.assertIn("id", result)
        execution = TestExecution.objects.get(pk=result["id"])

        self.assertEqual(result["assignee"], self.tester.pk)
        self.assertEqual(result["assignee"], execution.assignee.pk)

        self.assertEqual(result["tested_by"], self.new_user.pk)
        self.assertEqual(result["tested_by"], execution.tested_by.pk)

        self.assertEqual(result["case_text_version"], 123)
        self.assertEqual(result["case_text_version"], execution.case_text_version)

        self.assertEqual(result["start_date"], datetime(2026, 1, 19, 13, 0, 0))
        self.assertEqual(result["start_date"], execution.start_date)

        self.assertEqual(result["stop_date"], datetime(2026, 1, 19, 13, 10, 0))
        self.assertEqual(result["stop_date"], execution.stop_date)

        self.assertEqual(result["sortkey"], 10)
        self.assertEqual(result["sortkey"], execution.sortkey)

        self.assertEqual(result["run"], self.test_run.pk)
        self.assertEqual(result["run"], execution.run.pk)

        self.assertEqual(result["build"], self.test_run.build.pk)
        self.assertEqual(result["build"], execution.build.pk)

        self.assertEqual(result["case"], self.test_case.pk)
        self.assertEqual(result["case"], execution.case.pk)

        self.assertEqual(result["status"], execution.status.pk)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestExecution.create"'
        ):
            self.rpc_client.TestExecution.create(
                {
                    "assignee": self.tester.pk,
                    "tested_by": self.new_user.pk,
                    "case_text_version": 123,
                    "start_date": "2026-01-19 13:00:00",
                    "stop_date": "2026-01-19 13:10:00",
                    "sortkey": 10,
                    "run": self.test_run.pk,
                    "build": self.test_run.build.pk,
                    "case": self.test_case.pk,
                    "status": TestExecutionStatus.objects.first().pk,
                }
            )


class TestCreateWithEmptyFields(TestCreate):
    def verify_api_with_permission(self):
        result = self.rpc_client.TestExecution.create(
            {
                "case_text_version": 123,
                "sortkey": 10,
                "run": self.test_run.pk,
                "build": self.test_run.build.pk,
                "case": self.test_case.pk,
                "status": TestExecutionStatus.objects.last().pk,
                # note: these fields are deliberately left out
                # "assignee", "tested_by"
                # "start_date", "stop_date"
            }
        )

        self.assertIn("id", result)
        execution = TestExecution.objects.get(pk=result["id"])

        self.assertIsNone(result["assignee"])
        self.assertIsNone(execution.assignee)

        self.assertIsNone(result["tested_by"])
        self.assertIsNone(execution.tested_by)

        self.assertEqual(result["case_text_version"], 123)
        self.assertEqual(result["case_text_version"], execution.case_text_version)

        self.assertIsNone(result["start_date"])
        self.assertIsNone(execution.start_date)

        self.assertIsNone(result["stop_date"])
        self.assertIsNone(execution.stop_date)

        self.assertEqual(result["sortkey"], 10)
        self.assertEqual(result["sortkey"], execution.sortkey)

        self.assertEqual(result["run"], self.test_run.pk)
        self.assertEqual(result["run"], execution.run.pk)

        self.assertEqual(result["build"], self.test_run.build.pk)
        self.assertEqual(result["build"], execution.build.pk)

        self.assertEqual(result["case"], self.test_case.pk)
        self.assertEqual(result["case"], execution.case.pk)

        self.assertEqual(result["status"], execution.status.pk)
