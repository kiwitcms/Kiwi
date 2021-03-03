# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from django import test
from django.utils.translation import gettext_lazy as _
from mock import patch

from tcms.tests import BaseCaseRun
from tcms.tests.factories import TestCaseFactory, TestRunFactory


class Test_TestRun(BaseCaseRun):  # pylint: disable=invalid-name
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.empty_test_run = TestRunFactory(
            product_version=cls.version,
            plan=cls.plan,
            manager=cls.tester,
            default_tester=cls.tester,
        )

    @patch("tcms.core.utils.mailto.send_mail")
    def test_send_mail_after_test_run_creation(self, send_mail):
        test_run = TestRunFactory(plan=self.plan)

        recipients = test_run.get_notify_addrs()

        # Verify notification mail
        self.assertIn(
            _("NEW: TestRun #%(pk)d - %(summary)s")
            % {"pk": test_run.pk, "summary": test_run.summary},
            send_mail.call_args_list[0][0][0],
        )
        for recipient in recipients:
            self.assertIn(recipient, send_mail.call_args_list[0][0][-1])


class TestRunMethods(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.test_run = TestRunFactory()
        cls.test_case = TestCaseFactory()
        # we need 1 version in the history
        cls.test_case.save()

    def test_create_execution_without_status(self):
        execution = self.test_run.create_execution(self.test_case)

        self.assertEqual(execution.status.weight, 0)
        self.assertEqual(execution.status.name, _("IDLE"))
