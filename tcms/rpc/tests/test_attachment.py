# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used


from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.tests import user_should_have_perm
from tcms.tests.factories import TestPlanFactory
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestRemoveAttachment(APITestCase):
    """Test for Attachment.remove_attachment"""

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory()

    def test_remove_attachment(self):
        file_name = "attachment.txt"
        self.rpc_client.TestPlan.add_attachment(self.plan.pk, file_name, "a2l3aXRjbXM=")

        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)
        self.rpc_client.Attachment.remove_attachment(attachments[0]["pk"])
        attachments = self.rpc_client.TestPlan.list_attachments(self.plan.pk)

        self.assertEqual(0, len(attachments))


class TestRemoveAttachmentPermissions(APIPermissionsTestCase):
    """Test for Attachment.remove_attachment permissions"""

    permission_label = "attachments.delete_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory()
        user_should_have_perm(cls.tester, "attachments.add_attachment")
        user_should_have_perm(cls.tester, "attachments.view_attachment")

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
