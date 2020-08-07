# -*- coding: utf-8 -*-

from attachments.models import Attachment
from tcms.utils.permissions import initiate_user_with_default_setups

from tcms.tests import LoggedInTestCase
from tcms.tests.factories import TestPlanFactory


class TestPlanAttachments(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

        cls.plan = TestPlanFactory()

    def test_delete_testplan_deletes_attachments(self):
        self.attach_file_to('testplans.TestPlan', self.plan)
        attachments = Attachment.objects.attachments_for_object(self.plan)
        self.assertGreater(attachments.count(), 0)

        self.plan.delete()

        self.assertEqual(attachments.count(), 0)
