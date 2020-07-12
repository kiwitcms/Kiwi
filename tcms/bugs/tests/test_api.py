# pylint: disable=attribute-defined-outside-init
# pylint: disable=wrong-import-position
import unittest
from xmlrpc.client import Fault as XmlRPCFault
from xmlrpc.client import ProtocolError

from django.conf import settings

if "tcms.bugs.apps.AppConfig" not in settings.INSTALLED_APPS:
    raise unittest.SkipTest("tcms.bugs is disabled")

from tcms.bugs.models import Bug                                        # noqa: E402
from tcms.bugs.tests.factory import BugFactory                          # noqa: E402
from tcms.rpc.tests.utils import APITestCase, APIPermissionsTestCase    # noqa: E402
from tcms.tests.factories import TagFactory                             # noqa: E402


class TestAddTagPermissions(APIPermissionsTestCase):
    """Test Bug.add_tag"""

    permission_label = "bugs.add_bug_tags"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.bug = BugFactory()
        self.tag = TagFactory()

    def verify_api_with_permission(self):
        self.rpc_client.Bug.add_tag(self.bug.pk, self.tag.name)
        self.assertIn(self.tag, self.bug.tags.all())

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.Bug.add_tag(self.bug.pk, self.tag.name)


class TestAddTag(APITestCase):
    """Test Bug.add_tag"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.bug = BugFactory()
        self.tag = TagFactory()

    def test_add_tag_to_non_existent_bug(self):
        with self.assertRaisesRegex(XmlRPCFault, 'Bug matching query does not exist'):
            self.rpc_client.Bug.add_tag(-9, self.tag.name)


class TestRemoveTagPermissions(APIPermissionsTestCase):
    """Test Bug.remove_tag"""

    permission_label = "bugs.delete_bug_tags"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.bug = BugFactory()
        self.tag = TagFactory()
        self.bug.tags.add(self.tag)

    def verify_api_with_permission(self):
        self.rpc_client.Bug.remove_tag(self.bug.pk, self.tag.name)
        self.assertNotIn(self.tag, self.bug.tags.all())

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.Bug.remove_tag(self.bug.pk, self.tag.name)


class TestRemovePermissions(APIPermissionsTestCase):
    """Test permissions of Bug.remove"""

    permission_label = "bugs.delete_bug"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.bug = BugFactory()
        self.another_bug = BugFactory()
        self.yet_another_bug = BugFactory()

    def verify_api_with_permission(self):
        self.rpc_client.Bug.remove({"pk__in": [self.bug.pk, self.another_bug.pk]})

        bugs = Bug.objects.all()
        self.assertNotIn(self.bug, bugs)
        self.assertNotIn(self.another_bug, bugs)
        self.assertIn(self.yet_another_bug, bugs)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.Bug.remove({"pk__in": [self.bug.pk, self.another_bug.pk]})


class TestFilter(APITestCase):
    """Test Bug.filter"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.bug = BugFactory(status=False)
        self.another_bug = BugFactory(status=True)
        self.yet_another_bug = BugFactory(status=True)

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
