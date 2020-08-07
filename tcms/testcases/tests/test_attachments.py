# -*- coding: utf-8 -*-

from attachments.models import Attachment
from tcms.utils.permissions import initiate_user_with_default_setups

from tcms.tests import LoggedInTestCase
from tcms.tests.factories import TestCaseFactory


class TestCaseAttachments(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

        cls.case = TestCaseFactory()

    def test_delete_testcase_deletes_attachments(self):
        self.attach_file_to('testcases.TestCase', self.case)
        attachments = Attachment.objects.attachments_for_object(self.case)
        self.assertGreater(attachments.count(), 0)

        self.case.delete()

        self.assertEqual(attachments.count(), 0)
