# pylint: disable=attribute-defined-outside-init
# pylint: disable=wrong-import-position
import unittest
from xmlrpc.client import Fault as XmlRPCFault
from xmlrpc.client import ProtocolError

from django.conf import settings

if "tcms.bugs.apps.AppConfig" not in settings.INSTALLED_APPS:
    raise unittest.SkipTest("tcms.bugs is disabled")

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
