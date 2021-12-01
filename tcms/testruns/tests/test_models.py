# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from django import test
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from mock import patch
from parameterized import parameterized

from tcms.tests import BaseCaseRun
from tcms.tests.factories import TestCaseFactory, TestExecutionFactory, TestRunFactory


class Test_TestRun(BaseCaseRun):  # pylint: disable=invalid-name
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.empty_test_run = TestRunFactory(
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
        for execution in self.test_run.create_execution(self.test_case):
            self.assertEqual(execution.status.weight, 0)
            self.assertEqual(execution.status.name, _("IDLE"))


class TestExecutionActualDuration(TestCase):
    @parameterized.expand(
        [
            (
                "both_values_are_set",
                timezone.datetime(2021, 3, 22),
                timezone.datetime(2021, 3, 23),
                timezone.timedelta(days=1),
            ),
            ("both_values_are_none", None, None, None),
            ("start_date_is_none", None, timezone.datetime(2021, 3, 23), None),
            ("stop_date_is_none", timezone.datetime(2021, 3, 22), None, None),
        ]
    )
    def test_when(self, _name, start, stop, expected):
        execution = TestExecutionFactory(start_date=start, stop_date=stop)
        self.assertEqual(execution.actual_duration, expected)
