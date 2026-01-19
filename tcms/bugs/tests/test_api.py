# pylint: disable=attribute-defined-outside-init
# pylint: disable=wrong-import-position
import unittest
from datetime import datetime, timedelta

from attachments.models import Attachment
from django.conf import settings
from django.utils import timezone

from tcms.xmlrpc_wrapper import XmlRPCFault

if "tcms.bugs.apps.AppConfig" not in settings.INSTALLED_APPS:
    raise unittest.SkipTest("tcms.bugs is disabled")

from tcms.bugs.models import Bug  # noqa: E402
from tcms.bugs.models import Severity  # noqa: E402
from tcms.bugs.tests.factory import BugFactory  # noqa: E402
from tcms.core.helpers import comments
from tcms.rpc.tests.utils import APIPermissionsTestCase  # noqa: E402
from tcms.rpc.tests.utils import APITestCase
from tcms.tests import remove_perm_from_user, user_should_have_perm
from tcms.tests.factories import BuildFactory  # noqa: E402
from tcms.tests.factories import TagFactory  # noqa: E402
from tcms.tests.factories import TestExecutionFactory  # noqa: E402
from tcms.tests.factories import UserFactory  # noqa: E402


class TestAddTagPermissions(APIPermissionsTestCase):
    """Test Bug.add_tag"""

    permission_label = "bugs.add_bug_tags"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory()
        cls.tag = TagFactory()

    def verify_api_with_permission(self):
        self.rpc_client.Bug.add_tag(self.bug.pk, self.tag.name)
        self.assertIn(self.tag, self.bug.tags.all())

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.add_tag"'
        ):
            self.rpc_client.Bug.add_tag(self.bug.pk, self.tag.name)


class TestAddTag(APITestCase):
    """Test Bug.add_tag"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory()
        cls.tag = TagFactory()

    def test_add_tag_to_non_existent_bug(self):
        with self.assertRaisesRegex(XmlRPCFault, "Bug matching query does not exist"):
            self.rpc_client.Bug.add_tag(-9, self.tag.name)


class TestRemoveTagPermissions(APIPermissionsTestCase):
    """Test Bug.remove_tag"""

    permission_label = "bugs.delete_bug_tags"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory()
        cls.tag = TagFactory()
        cls.bug.tags.add(cls.tag)

    def verify_api_with_permission(self):
        self.rpc_client.Bug.remove_tag(self.bug.pk, self.tag.name)
        self.assertNotIn(self.tag, self.bug.tags.all())

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.remove_tag"'
        ):
            self.rpc_client.Bug.remove_tag(self.bug.pk, self.tag.name)


class TestRemovePermissions(APIPermissionsTestCase):
    """Test permissions of Bug.remove"""

    permission_label = "bugs.delete_bug"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory()
        cls.another_bug = BugFactory()
        cls.yet_another_bug = BugFactory()

    def verify_api_with_permission(self):
        self.rpc_client.Bug.remove({"pk__in": [self.bug.pk, self.another_bug.pk]})

        bugs = Bug.objects.all()
        self.assertNotIn(self.bug, bugs)
        self.assertNotIn(self.another_bug, bugs)
        self.assertIn(self.yet_another_bug, bugs)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.remove"'
        ):
            self.rpc_client.Bug.remove({"pk__in": [self.bug.pk, self.another_bug.pk]})


class TestBugFilter(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory(status=False)
        cls.another_bug = BugFactory(status=True)
        cls.yet_another_bug = BugFactory(status=True)

    def test_filter(self):
        result = self.rpc_client.Bug.filter({"status": True})
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        pks = []
        for item in result:
            pks.append(item["pk"])

        self.assertNotIn(self.bug.pk, pks)
        self.assertIn(self.another_bug.pk, pks)
        self.assertIn(self.yet_another_bug.pk, pks)

    def test_filter_non_existing(self):
        result = self.rpc_client.Bug.filter({"pk": -99})
        self.assertEqual(len(result), 0)


class TestBugFilterCanonical(APIPermissionsTestCase):
    permission_label = "bugs.view_bug"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory(status=False)
        cls.another_bug = BugFactory(status=True)
        cls.yet_another_bug = BugFactory(status=True)

    def verify_api_with_permission(self):
        result = self.rpc_client.Bug.filter_canonical(
            {
                "id": self.bug.pk,
            }
        )[0]

        self.assertEqual(result["id"], self.bug.id)
        self.assertEqual(result["summary"], self.bug.summary)
        self.assertEqual(result["created_at"], self.bug.created_at)
        self.assertEqual(result["status"], self.bug.status)
        self.assertEqual(result["reporter"], self.bug.reporter_id)
        self.assertEqual(result["assignee"], self.bug.assignee_id)
        self.assertEqual(result["product"], self.bug.product_id)
        self.assertEqual(result["version"], self.bug.version_id)
        self.assertEqual(result["build"], self.bug.build_id)
        self.assertEqual(result["severity"], self.bug.severity_id)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.filter_canonical"'
        ):
            self.rpc_client.Bug.filter_canonical({})


class TestBugCreate(APIPermissionsTestCase):
    permission_label = "bugs.add_bug"

    def verify_api_with_permission(self):
        reporter = UserFactory()
        build = BuildFactory()
        severity, _ = Severity.objects.get_or_create(
            name="Low",
            weight=0,
            icon="fa fa-volume-down",
            color="#ff0f1f",
        )

        result = self.rpc_client.Bug.create(
            {
                "summary": "A bug created via API",
                "status": False,
                "reporter": reporter.pk,
                "product": build.version.product_id,
                "version": build.version_id,
                "build": build.pk,
                "severity": severity.pk,
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["summary"], "A bug created via API")
        self.assertGreater(result["created_at"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["created_at"], timezone.now() + timedelta(seconds=1))
        self.assertEqual(result["status"], False)
        self.assertEqual(result["reporter"], reporter.pk)
        self.assertEqual(result["product"], build.version.product_id)
        self.assertEqual(result["version"], build.version_id)
        self.assertEqual(result["build"], build.pk)
        self.assertEqual(result["severity"], severity.pk)

        # verify the object from the DB
        bug = Bug.objects.get(pk=result["id"])
        self.assertEqual(bug.summary, result["summary"])
        self.assertEqual(bug.created_at, result["created_at"])
        self.assertEqual(bug.status, result["status"])
        self.assertEqual(bug.reporter_id, result["reporter"])
        self.assertEqual(bug.product_id, result["product"])
        self.assertEqual(bug.version_id, result["version"])
        self.assertEqual(bug.build_id, result["build"])
        self.assertEqual(bug.severity_id, result["severity"])

    def verify_api_without_permission(self):
        build = BuildFactory()
        severity, _ = Severity.objects.get_or_create(
            name="High",
            weight=100,
            icon="fa fa-volume-up",
            color="#2ba150",
        )

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.create"'
        ):
            self.rpc_client.Bug.create(
                {
                    "summary": "A bug created via API",
                    "status": False,
                    "reporter": self.tester.pk,
                    "product": build.version.product_id,
                    "version": build.version_id,
                    "build": build.pk,
                    "severity": severity.pk,
                }
            )


class TestBugCreateOverrideSomeValues(TestBugCreate):
    def verify_api_with_permission(self):
        build = BuildFactory()
        severity, _ = Severity.objects.get_or_create(
            name="Low",
            weight=0,
            icon="fa fa-volume-down",
            color="#ff0f1f",
        )

        result = self.rpc_client.Bug.create(
            {
                "summary": "A bug created via API",
                "product": build.version.product_id,
                "version": build.version_id,
                "build": build.pk,
                "severity": severity.pk,
                # values below are overriden
                "created_at": "2026-01-04 00:00:00",
                # status is not provided, should default to True
                # reporter not provided, should be self.tester
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["created_at"], datetime(2026, 1, 4, 0, 0, 0))
        self.assertEqual(result["status"], True)
        self.assertEqual(result["reporter"], self.tester.pk)

        # verify the object from the DB
        bug = Bug.objects.get(pk=result["id"])
        self.assertEqual(bug.created_at, result["created_at"])
        self.assertEqual(bug.status, result["status"])
        self.assertEqual(bug.reporter_id, result["reporter"])


class TestSeverityCreate(APIPermissionsTestCase):
    permission_label = "bugs.add_severity"

    def verify_api_with_permission(self):
        result = self.rpc_client.Severity.create(
            {
                "name": "Blocker",
                "weight": 50,
                "icon": "fa fa-ban",
                "color": "#ff0f1f",
            }
        )

        # verify the serialized result
        self.assertIn("id", result)
        self.assertEqual(result["name"], "Blocker")
        self.assertEqual(result["weight"], 50)
        self.assertEqual(result["icon"], "fa fa-ban")
        self.assertEqual(result["color"], "#ff0f1f")

        # verify the object from the DB
        severity = Severity.objects.get(pk=result["id"])
        self.assertEqual(severity.name, result["name"])
        self.assertEqual(severity.weight, result["weight"])
        self.assertEqual(severity.icon, result["icon"])
        self.assertEqual(severity.color, result["color"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Severity.create"'
        ):
            self.rpc_client.Severity.create(
                {
                    "name": "Minor",
                    "weight": 0,
                    "icon": "fa fa-meh-o",
                    "color": "#e3dada",
                }
            )


class TestSeverityFilter(APIPermissionsTestCase):
    permission_label = "bugs.view_severity"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.severity, _ = Severity.objects.get_or_create(
            name="Low",
            weight=0,
            icon="fa fa-volume-down",
            color="#ff0f1f",
        )

        _high, _ = Severity.objects.get_or_create(
            name="High",
            weight=100,
            icon="fa fa-volume-up",
            color="#2ba150",
        )

    def verify_api_with_permission(self):
        result = self.rpc_client.Severity.filter(
            {
                "pk": self.severity.pk,
            }
        )[0]

        self.assertEqual(result["id"], self.severity.id)
        self.assertEqual(result["name"], self.severity.name)
        self.assertEqual(result["weight"], self.severity.weight)
        self.assertEqual(result["icon"], self.severity.icon)
        self.assertEqual(result["color"], self.severity.color)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Severity.filter"'
        ):
            self.rpc_client.Severity.filter({})


class TestBugGetComments(APIPermissionsTestCase):
    permission_label = "django_comments.view_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory(status=False)
        _ = comments.add_comment([cls.bug], "Hello World", cls.tester)
        _ = comments.add_comment([cls.bug], "Happy Testing", UserFactory())

    def verify_api_with_permission(self):
        result = self.rpc_client.Bug.get_comments(self.bug.pk)
        self.assertEqual(len(result), 2)

        for comment in result:
            self.assertIn("id", comment)
            self.assertIn(comment["comment"], ("Hello World", "Happy Testing"))
            self.assertEqual(comment["is_public"], True)
            self.assertEqual(comment["object_pk"], str(self.bug.pk))
            self.assertIn("user_id", comment)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.get_comments"'
        ):
            self.rpc_client.Bug.get_comments(self.bug.pk)


class TestBugAddComment(APIPermissionsTestCase):
    permission_label = "django_comments.add_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory(status=False)

    def verify_api_with_permission(self):
        result = self.rpc_client.Bug.add_comment(self.bug.pk, "Hello World")

        self.assertIn("id", result)
        self.assertEqual(result["comment"], "Hello World")
        self.assertEqual(result["is_public"], True)
        self.assertEqual(result["object_pk"], self.bug.pk)
        self.assertEqual(result["user"], self.tester.pk)
        self.assertGreater(result["submit_date"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["submit_date"], timezone.now() + timedelta(seconds=1))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.add_comment"'
        ):
            self.rpc_client.Bug.add_comment(self.bug.pk, "Happy Testing")


class BugAddCommentFromRegularUser(TestBugAddComment):
    def verify_api_with_permission(self):
        new_user = UserFactory()

        # try overriding comment author
        result = self.rpc_client.Bug.add_comment(
            self.bug.pk, "Hello World", new_user.pk
        )

        self.assertEqual(result["comment"], "Hello World")
        self.assertEqual(result["is_public"], True)
        self.assertEqual(result["object_pk"], self.bug.pk)
        self.assertEqual(result["user"], self.tester.pk)
        self.assertGreater(result["submit_date"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["submit_date"], timezone.now() + timedelta(seconds=1))

        # try overriding comment submit_date
        result = self.rpc_client.Bug.add_comment(
            self.bug.pk, "Happy Testing", new_user.pk, datetime(2026, 1, 4, 0, 0, 0)
        )

        self.assertEqual(result["comment"], "Happy Testing")
        self.assertEqual(result["object_pk"], self.bug.pk)
        self.assertEqual(result["user"], self.tester.pk)
        self.assertGreater(result["submit_date"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["submit_date"], timezone.now() + timedelta(seconds=1))


class BugAddCommentFromSuperUser(TestBugAddComment):
    def verify_api_with_permission(self):
        self.tester.is_superuser = True
        self.tester.save()

        new_user = UserFactory()

        # try overriding comment author
        result = self.rpc_client.Bug.add_comment(
            self.bug.pk, "Hello World", new_user.pk
        )

        self.assertEqual(result["comment"], "Hello World")
        self.assertEqual(result["is_public"], True)
        self.assertEqual(result["object_pk"], self.bug.pk)
        self.assertEqual(result["user"], new_user.pk)
        self.assertGreater(result["submit_date"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["submit_date"], timezone.now() + timedelta(seconds=1))

        # try overriding comment submit_date
        result = self.rpc_client.Bug.add_comment(
            self.bug.pk, "Happy Testing", new_user.pk, datetime(2026, 1, 4, 0, 0, 0)
        )

        self.assertEqual(result["comment"], "Happy Testing")
        self.assertEqual(result["object_pk"], self.bug.pk)
        self.assertEqual(result["user"], new_user.pk)
        self.assertEqual(result["submit_date"], datetime(2026, 1, 4, 0, 0, 0))


class TestBugAddAttachment(APIPermissionsTestCase):
    permission_label = "attachments.add_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory()

    def verify_api_with_permission(self):
        file_name = "report.txt"
        self.rpc_client.Bug.add_attachment(self.bug.pk, file_name, "a2l3aXRjbXM=")
        result = Attachment.objects.attachments_for_object(self.bug)
        self.assertEqual(1, len(result))

        attachment = result[0]
        file_url = attachment.attachment_file.url
        self.assertTrue(file_url.startswith("/uploads/attachments/bugs_bug/"))
        self.assertTrue(file_url.endswith(file_name))
        self.assertEqual(attachment.creator, self.tester)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.add_attachment"'
        ):
            self.rpc_client.Bug.add_attachment(
                self.bug.pk, "attachment.txt", "a2l3aXRjbXM="
            )


class TestBugListAttachments(APIPermissionsTestCase):
    permission_label = "attachments.view_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory()

    def verify_api_with_permission(self):
        user_should_have_perm(self.tester, "attachments.add_attachment")
        self.rpc_client.Bug.add_attachment(
            self.bug.pk, "bug_report.txt", "a2l3aXRjbXM="
        )
        remove_perm_from_user(self.tester, "attachments.add_attachment")

        result = self.rpc_client.Bug.list_attachments(self.bug.pk)
        self.assertEqual(len(result), 1)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "Bug.list_attachments"',
        ):
            self.rpc_client.Bug.list_attachments(self.bug.pk)


class TestAddExecution(APIPermissionsTestCase):
    permission_label = "bugs.add_bug_executions"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.bug = BugFactory()
        cls.execution = TestExecutionFactory()

    def verify_api_with_permission(self):
        self.assertEqual(self.bug.executions.count(), 0)

        self.rpc_client.Bug.add_execution(self.bug.pk, self.execution.pk)
        self.assertEqual(self.bug.executions.count(), 1)
        self.assertIn(self.execution, self.bug.executions.all())

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "Bug.add_execution"'
        ):
            self.rpc_client.Bug.add_execution(self.bug.pk, self.execution.pk)
