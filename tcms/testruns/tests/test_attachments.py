# -*- coding: utf-8 -*-

from attachments.models import Attachment
from tcms.utils.permissions import initiate_user_with_default_setups

from tcms.tests import LoggedInTestCase
from tcms.tests.factories import TestExecutionFactory, TestRunFactory


class TestRunAttachments(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

        cls.test_run = TestRunFactory()
        cls.execution = TestExecutionFactory(run=cls.test_run)

    def test_delete_testrun_deletes_attachments(self):
        self.attach_file_to('testruns.TestRun', self.test_run)
        attachments_for_run = Attachment.objects.attachments_for_object(self.test_run)
        self.assertGreater(attachments_for_run.count(), 0)

        self.attach_file_to('testruns.TestExecution', self.execution)
        attachments_for_execution = Attachment.objects.attachments_for_object(self.execution)
        self.assertGreater(attachments_for_execution.count(), 0)

        # will cascade-delete self.execution
        self.test_run.delete()

        self.assertEqual(attachments_for_run.count(), 0)
        self.assertEqual(attachments_for_execution.count(), 0)
