# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, attribute-defined-outside-init, objects-update-used

import time
from xmlrpc.client import Fault as XmlRPCFault

from django.forms.models import model_to_dict
from django.test import override_settings
from django.utils import timezone

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers import comments
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testruns.models import TestExecutionStatus
from tcms.tests.factories import (
    BuildFactory,
    LinkReferenceFactory,
    TestExecutionFactory,
    UserFactory,
)


class TestExecutionGetComments(APITestCase):
    """Test TestExecution.get_comments"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.comments = ["Text for first comment", "Text for second comment"]

        self.execution = TestExecutionFactory()
        for comment in self.comments:
            comments.add_comment([self.execution], comment, self.api_user)

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

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()
        self.comments = ["Text for first comment", "Text for second comment"]

        for comment in self.comments:
            comments.add_comment([self.execution], comment, self.tester)

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


class TestExecutionAddComment(APITestCase):
    """Test TestExecution.add_comment"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_2 = TestExecutionFactory()

    def test_add_comment_with_pk_as_int(self):
        created_comment = self.rpc_client.TestExecution.add_comment(
            self.execution_2.pk, "Hello World!"
        )
        execution_comments = comments.get_comments(self.execution_2)
        self.assertEqual(1, execution_comments.count())

        first_comment = execution_comments.first()
        self.assertEqual("Hello World!", first_comment.comment)
        self.assertEqual(created_comment["comment"], first_comment.comment)


class TestExecutionRemoveComment(APITestCase):
    """Test TestExecution.remove_comment"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.user = UserFactory()
        self.execution = TestExecutionFactory()

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

    def _fixture_setup(self):
        super()._fixture_setup()

        self.user = UserFactory()
        self.execution = TestExecutionFactory()

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

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()

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

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()

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
    def _fixture_setup(self):
        super()._fixture_setup()

        self.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        self.tester = UserFactory()
        self.execution = TestExecutionFactory(
            assignee=self.tester, tested_by=None, sortkey=10, status=self.status_idle
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
    def _fixture_setup(self):
        super()._fixture_setup()

        self.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        self.tester = UserFactory()
        self.execution = TestExecutionFactory(
            assignee=self.tester, tested_by=None, sortkey=10, status=self.status_idle
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
    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution_1 = TestExecutionFactory()
        self.execution_2 = TestExecutionFactory()

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
    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()

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

    permission_label = "testruns.view_testexecution"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.execution = TestExecutionFactory()

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
    def _fixture_setup(self):
        super()._fixture_setup()

        self.user = UserFactory()
        self.build = BuildFactory()
        self.execution_1 = TestExecutionFactory()
        self.execution_2 = TestExecutionFactory()
        self.status_positive = TestExecutionStatus.objects.filter(weight__gt=0).last()

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
        self.rpc_client.Auth.logout()
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestExecution.update"'
        ):
            self.rpc_client.TestExecution.update(
                self.execution_1.pk, {"stop_date": timezone.now()}
            )


class TestExecutionUpdateStatus(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.user = UserFactory()
        self.execution_1 = TestExecutionFactory()
        self.status_positive = TestExecutionStatus.objects.filter(weight__gt=0).last()
        self.status_negative = TestExecutionStatus.objects.filter(weight__lt=0).last()
        self.status_in_progress = TestExecutionStatus.objects.filter(weight=0).last()

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
