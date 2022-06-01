# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used

from xmlrpc.client import Fault as XmlRPCFault

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.tests import user_should_have_perm
from tcms.tests.factories import TestPlanFactory


class TestRemoveAttachment(APITestCase):
    """Test for Attachment.remove_attachment"""

    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()
        file_name = "attachment.txt"
        self.rpc_client.TestPlan.add_attachment(self.plan.pk, file_name, "a2l3aXRjbXM=")

    def test_remove_attachment(self):
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)
        self.rpc_client.Attachment.remove_attachment(attachments[0]["pk"])
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)

        self.assertEqual(0, len(attachments))


class TestRemoveAttachmentPermissions(APIPermissionsTestCase):
    """Test for Attachment.remove_attachment permissions"""

    permission_label = "attachments.delete_attachment"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()
        user_should_have_perm(self.tester, "attachments.add_attachment")
        user_should_have_perm(self.tester, "attachments.view_attachment")

    def verify_api_with_permission(self):
        file_name = "attachment.txt"
        self.rpc_client.TestPlan.add_attachment(self.plan.pk, file_name, "a2l3aXRjbXM=")
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)

        self.assertEqual(1, len(attachments))

        self.rpc_client.Attachment.remove_attachment(attachments[0]["pk"])
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)

        self.assertEqual(0, len(attachments))

    def verify_api_without_permission(self):
        file_name = "attachment.txt"
        self.rpc_client.TestPlan.add_attachment(self.plan.pk, file_name, "a2l3aXRjbXM=")
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)

        self.assertEqual(1, len(attachments))

        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "Attachment.remove_attachment"',
        ):
            self.rpc_client.Attachment.remove_attachment(attachments[0]["pk"])
