# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from mock import patch

from django.utils.translation import ugettext_lazy as _

from tcms.tests import BaseCaseRun
from tcms.tests.factories import TestRunFactory
from tcms.testcases.models import BugSystem


class Test_TestRun(BaseCaseRun):  # pylint: disable=invalid-name
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        bug_tracker = BugSystem.objects.first()
        cls.empty_test_run = TestRunFactory(product_version=cls.version,
                                            plan=cls.plan,
                                            manager=cls.tester,
                                            default_tester=cls.tester)

        # Add bugs to case runs
        cls.execution_1.add_bug('12345', bug_tracker.pk)
        cls.execution_1.add_bug('909090', bug_tracker.pk)
        cls.execution_3.add_bug('4567890', bug_tracker.pk)

    def test_get_bugs_count_if_no_bugs_added(self):
        self.assertEqual(0, self.empty_test_run.get_bug_count())

    def test_get_bugs_count(self):
        self.assertEqual(3, self.test_run.get_bug_count())

    @patch('tcms.core.utils.mailto.send_mail')
    def test_send_mail_after_test_run_creation(self, send_mail):
        test_run = TestRunFactory(plan=self.plan)

        recipients = test_run.get_notify_addrs()

        # Verify notification mail
        self.assertIn(_("NEW: TestRun #%(pk)d - %(summary)s") %
                      {'pk': test_run.pk, 'summary': test_run.summary},
                      send_mail.call_args_list[0][0][0])
        for recipient in recipients:
            self.assertIn(recipient, send_mail.call_args_list[0][0][-1])
