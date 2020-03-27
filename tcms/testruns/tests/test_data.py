# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

from datetime import datetime

from tcms.core.helpers.comments import add_comment
from tcms.testruns.data import TestExecutionDataMixin
from tcms.tests import BaseCaseRun, BasePlanCase
from tcms.tests.factories import (TestExecutionFactory, TestExecutionStatus,
                                  TestRunFactory)


class TestGetCaseRunsStatsByStatusFromEmptyTestRun(BasePlanCase):

    @classmethod
    def setUpTestData(cls):
        super(TestGetCaseRunsStatsByStatusFromEmptyTestRun, cls).setUpTestData()

        cls.empty_test_run = TestRunFactory(manager=cls.tester, default_tester=cls.tester,
                                            plan=cls.plan)

        cls.statuss = TestExecutionStatus.objects.all().order_by('pk')

    def test_get_from_empty_case_runs(self):
        data = self.empty_test_run.stats_executions_status(self.statuss)

        subtotal = dict((status.pk, [0, status])
                        for status in self.statuss)

        self.assertEqual(subtotal, data.StatusSubtotal)
        self.assertEqual(0, data.CaseRunsTotalCount)
        self.assertEqual(.0, data.CompletedPercentage)
        self.assertEqual(.0, data.FailurePercentage)


class TestGetCaseRunsStatsByStatus(BasePlanCase):

    @classmethod
    def setUpTestData(cls):
        super(TestGetCaseRunsStatsByStatus, cls).setUpTestData()

        cls.statuss = TestExecutionStatus.objects.all().order_by('pk')

        cls.status_idle = TestExecutionStatus.objects.filter(weight=0).first()
        cls.status_failed = TestExecutionStatus.objects.filter(weight__lt=0).first()
        cls.status_waived = TestExecutionStatus.objects.filter(weight__gt=0).first()

        cls.test_run = TestRunFactory(product_version=cls.version, plan=cls.plan,
                                      manager=cls.tester, default_tester=cls.tester)

        for case, status in ((cls.case_1, cls.status_idle),
                             (cls.case_2, cls.status_failed),
                             (cls.case_3, cls.status_failed),
                             (cls.case_4, cls.status_waived),
                             (cls.case_5, cls.status_waived),
                             (cls.case_6, cls.status_waived)):
            TestExecutionFactory(assignee=cls.tester, tested_by=cls.tester,
                                 run=cls.test_run, case=case, status=status)

    def test_get_stats(self):
        data = self.test_run.stats_executions_status(self.statuss)

        subtotal = dict((status.pk, [0, status])
                        for status in self.statuss)
        subtotal[self.status_idle.pk][0] = 1
        subtotal[self.status_failed.pk][0] = 2
        subtotal[self.status_waived.pk][0] = 3

        expected_completed_percentage = 5.0 * 100 / 6
        expected_failure_percentage = 2.0 * 100 / 6

        self.assertEqual(subtotal, data.StatusSubtotal)
        self.assertEqual(6, data.CaseRunsTotalCount)
        self.assertEqual(expected_completed_percentage, data.CompletedPercentage)
        self.assertEqual(expected_failure_percentage, data.FailurePercentage)


class TestGetExecutionComments(BaseCaseRun):
    """Test TestExecutionDataMixin.get_caseruns_comments

    There are two test runs created already, cls.test_run and cls.test_run_1.

    For this case, comments will be added to cls.test_run_1 in order to ensure
    comments could be retrieved correctly. And another one is for ensuring
    empty result even if no comment is added.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.submit_date = datetime(2017, 7, 7, 7, 7, 7)

        add_comment([cls.execution_4, cls.execution_5],
                    comments='new comment',
                    user=cls.tester,
                    submit_date=cls.submit_date)
        add_comment([cls.execution_4],
                    comments='make better',
                    user=cls.tester,
                    submit_date=cls.submit_date)

    def test_get_empty_comments_if_no_comment_there(self):
        data = TestExecutionDataMixin()
        comments = data.get_execution_comments(self.test_run.pk)
        self.assertEqual({}, comments)

    def test_get_comments(self):
        data = TestExecutionDataMixin()
        comments = data.get_execution_comments(self.test_run_1.pk)

        # note: keys are integer but the values are all string
        expected_comments = {
            self.execution_4.pk: [
                {
                    'execution_id': str(self.execution_4.pk),
                    'user_name': self.tester.username,
                    'submit_date': self.submit_date,
                    'comment': 'new comment'
                },
                {
                    'execution_id': str(self.execution_4.pk),
                    'user_name': self.tester.username,
                    'submit_date': self.submit_date,
                    'comment': 'make better'
                }
            ],
            self.execution_5.pk: [
                {
                    'execution_id': str(self.execution_5.pk),
                    'user_name': self.tester.username,
                    'submit_date': self.submit_date,
                    'comment': 'new comment'
                }
            ]
        }

        for exp_key in expected_comments:
            for exp_cmt in expected_comments[exp_key]:
                self.assertIn(exp_cmt, comments[exp_key])
