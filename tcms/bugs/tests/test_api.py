# pylint: disable=attribute-defined-outside-init
# pylint: disable=wrong-import-position
import unittest

from django.conf import settings

from tcms.xmlrpc_wrapper import XmlRPCFault

if "tcms.bugs.apps.AppConfig" not in settings.INSTALLED_APPS:
    raise unittest.SkipTest("tcms.bugs is disabled")

from tcms.bugs.models import Bug, Severity  # noqa: E402
from tcms.bugs.tests.factory import BugFactory  # noqa: E402
from tcms.rpc.tests.utils import APIPermissionsTestCase  # noqa: E402
from tcms.rpc.tests.utils import APITestCase
from tcms.tests.factories import TagFactory  # noqa: E402


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
