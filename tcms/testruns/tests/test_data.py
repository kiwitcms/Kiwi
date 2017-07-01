# -*- coding: utf-8 -*-

from tcms.testcases.models import TestCaseBugSystem
from tcms.testruns.data import TestCaseRunDataMixin
from tcms.testruns.data import get_run_bug_ids
from tcms.testruns.data import stats_caseruns_status
from tcms.tests import BaseCaseRun
from tcms.tests import BasePlanCase
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestCaseRunStatus
from tcms.tests.factories import TestRunFactory


class TestGetCaseRunsStatsByStatusFromEmptyTestRun(BasePlanCase):

    @classmethod
    def setUpTestData(cls):
        super(TestGetCaseRunsStatsByStatusFromEmptyTestRun, cls).setUpTestData()

        cls.empty_test_run = TestRunFactory(manager=cls.tester, default_tester=cls.tester,
                                            plan=cls.plan)

        cls.case_run_statuss = TestCaseRunStatus.objects.all().order_by('pk')

    def test_get_from_empty_case_runs(self):
        data = stats_caseruns_status(self.empty_test_run.pk,
                                     self.case_run_statuss)

        subtotal = dict((status.pk, [0, status])
                        for status in self.case_run_statuss)

        self.assertEqual(subtotal, data.StatusSubtotal)
        self.assertEqual(0, data.CaseRunsTotalCount)
        self.assertEqual(.0, data.CompletedPercentage)
        self.assertEqual(.0, data.FailurePercentage)


class TestGetCaseRunsStatsByStatus(BasePlanCase):

    @classmethod
    def setUpTestData(cls):
        super(TestGetCaseRunsStatsByStatus, cls).setUpTestData()

        cls.case_run_statuss = TestCaseRunStatus.objects.all().order_by('pk')

        cls.case_run_status_idle = TestCaseRunStatus.objects.get(name='IDLE')
        cls.case_run_status_failed = TestCaseRunStatus.objects.get(name='FAILED')
        cls.case_run_status_waived = TestCaseRunStatus.objects.get(name='WAIVED')

        cls.test_run = TestRunFactory(product_version=cls.version, plan=cls.plan,
                                      manager=cls.tester, default_tester=cls.tester)

        for case, status in ((cls.case_1, cls.case_run_status_idle),
                             (cls.case_2, cls.case_run_status_failed),
                             (cls.case_3, cls.case_run_status_failed),
                             (cls.case_4, cls.case_run_status_waived),
                             (cls.case_5, cls.case_run_status_waived),
                             (cls.case_6, cls.case_run_status_waived)):
            TestCaseRunFactory(assignee=cls.tester, tested_by=cls.tester,
                               run=cls.test_run, case=case, case_run_status=status)

    def test_get_stats(self):
        data = stats_caseruns_status(self.test_run.pk, self.case_run_statuss)

        subtotal = dict((status.pk, [0, status])
                        for status in self.case_run_statuss)
        subtotal[self.case_run_status_idle.pk][0] = 1
        subtotal[self.case_run_status_failed.pk][0] = 2
        subtotal[self.case_run_status_waived.pk][0] = 3

        expected_completed_percentage = 5.0 * 100 / 6
        expected_failure_percentage = 2.0 * 100 / 5

        self.assertEqual(subtotal, data.StatusSubtotal)
        self.assertEqual(6, data.CaseRunsTotalCount)
        self.assertEqual(expected_completed_percentage, data.CompletedPercentage)
        self.assertEqual(expected_failure_percentage, data.FailurePercentage)


class TestGetRunBugIDs(BaseCaseRun):
    """Test get_run_bug_ids"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetRunBugIDs, cls).setUpTestData()

        cls.bugzilla = TestCaseBugSystem.objects.get(name='Bugzilla')

        cls.case_run_1.add_bug('123456', bug_system_id=cls.bugzilla.pk)
        cls.case_run_1.add_bug('100000', bug_system_id=cls.bugzilla.pk)
        cls.case_run_1.add_bug('100001', bug_system_id=cls.bugzilla.pk)
        cls.case_run_2.add_bug('100001', bug_system_id=cls.bugzilla.pk)

    def test_get_bug_ids_when_no_bug_is_added(self):
        bug_ids = get_run_bug_ids(self.test_run_1.pk)
        self.assertEqual(0, len(bug_ids))

    def test_get_bug_ids(self):
        bug_ids = get_run_bug_ids(self.test_run.pk)

        self.assertEqual(3, len(bug_ids))

        # Convert result to dict in order to compare the equivalence easily

        expected = {
            '123456': self.bugzilla.url_reg_exp % '123456',
            '100000': self.bugzilla.url_reg_exp % '100000',
            '100001': self.bugzilla.url_reg_exp % '100001',
        }
        self.assertEqual(expected, dict(bug_ids))


class TestGetCaseRunsBugs(BaseCaseRun):
    """Test TestCaseRunDataMixin.get_caseruns_bugs"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetCaseRunsBugs, cls).setUpTestData()

        cls.bugzilla = TestCaseBugSystem.objects.get(name='Bugzilla')
        cls.jira = TestCaseBugSystem.objects.get(name='JIRA')

        cls.bz_bug_1 = '12345'
        cls.case_run_1.add_bug(cls.bz_bug_1, bug_system_id=cls.bugzilla.pk)
        cls.bz_bug_2 = '10000'
        cls.case_run_1.add_bug(cls.bz_bug_2, bug_system_id=cls.bugzilla.pk)
        cls.jira_nitrate_1 = 'NITRATE-1'
        cls.case_run_1.add_bug(cls.jira_nitrate_1, bug_system_id=cls.jira.pk)
        cls.jira_nitrate_2 = 'NITRATE-2'
        cls.case_run_2.add_bug(cls.jira_nitrate_2, bug_system_id=cls.jira.pk)

    def test_empty_if_no_bugs(self):
        data = TestCaseRunDataMixin()
        result = data.get_caseruns_bugs(self.test_run_1.pk)
        self.assertEqual({}, result)

    def test_get_bugs(self):
        data = TestCaseRunDataMixin()
        result = data.get_caseruns_bugs(self.test_run.pk)
        expected_result = {
            self.case_run_1.pk: [
                {
                    'bug_id': self.bz_bug_1,
                    'case_run': self.case_run_1.pk,
                    'bug_system__url_reg_exp': self.bugzilla.url_reg_exp,
                    'bug_url': self.bugzilla.url_reg_exp % self.bz_bug_1,
                },
                {
                    'bug_id': self.bz_bug_2,
                    'case_run': self.case_run_1.pk,
                    'bug_system__url_reg_exp': self.bugzilla.url_reg_exp,
                    'bug_url': self.bugzilla.url_reg_exp % self.bz_bug_2,
                },
                {
                    'bug_id': self.jira_nitrate_1,
                    'case_run': self.case_run_1.pk,
                    'bug_system__url_reg_exp': self.jira.url_reg_exp,
                    'bug_url': self.jira.url_reg_exp % self.jira_nitrate_1,
                }
            ],
            self.case_run_2.pk: [
                {
                    'bug_id': self.jira_nitrate_2,
                    'case_run': self.case_run_2.pk,
                    'bug_system__url_reg_exp': self.jira.url_reg_exp,
                    'bug_url': self.jira.url_reg_exp % self.jira_nitrate_2,
                }
            ],
        }
        self.assertEqual(expected_result, result)
