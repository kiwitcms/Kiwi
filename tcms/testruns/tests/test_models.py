# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from mock import patch

from tcms.tests import BaseCaseRun
from tcms.tests.factories import TestRunFactory
from tcms.testcases.models import BugSystem


class TestRunGetBugsCount(BaseCaseRun):
    """Test TestRun.get_bug_count"""

    @classmethod
    def setUpTestData(cls):
        super(TestRunGetBugsCount, cls).setUpTestData()

        bug_tracker = BugSystem.objects.first()
        cls.empty_test_run = TestRunFactory(product_version=cls.version,
                                            plan=cls.plan,
                                            manager=cls.tester,
                                            default_tester=cls.tester)

        # Add bugs to case runs
        cls.case_run_1.add_bug('12345', bug_tracker.pk)
        cls.case_run_1.add_bug('909090', bug_tracker.pk)
        cls.case_run_3.add_bug('4567890', bug_tracker.pk)

    def test_get_bugs_count_if_no_bugs_added(self):
        self.assertEqual(0, self.empty_test_run.get_bug_count())

    def test_get_bugs_count(self):
        self.assertEqual(3, self.test_run.get_bug_count())

    @patch('tcms.core.utils.mailto.send_mail')
    def test_send_mail_after_test_run_creation(self, send_mail):
        test_run = TestRunFactory()

        recipients = test_run.get_notify_addrs()

        # Verify notification mail
        self.assertIn("NEW: TestRun #%d - %s" % (test_run.pk, test_run.summary),
                      send_mail.call_args_list[0][0][0])
        self.assertIn("Summary: %s" % test_run.summary, send_mail.call_args_list[0][0][1])
        for recipient in recipients:
            self.assertIn(recipient, send_mail.call_args_list[0][0][-1])
