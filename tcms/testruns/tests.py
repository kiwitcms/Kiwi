# -*- coding: utf-8 -*-

from six.moves import http_client

from django import test
from django.core.urlresolvers import reverse

from tcms.testruns.data import stats_caseruns_status
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.testruns.models import TestRun
from tcms.tests import BaseCaseRun
from tcms.tests import BasePlanCase
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestRunFactory


# ### Test cases for View methods ###


class TestOrderCases(BaseCaseRun):
    """Test view method order_case"""

    @classmethod
    def setUpTestData(cls):
        super(TestOrderCases, cls).setUpTestData()

        cls.client = test.Client()

    def test_404_if_run_does_not_exist(self):
        nonexisting_run_pk = TestRun.objects.count() + 1
        url = reverse('tcms.testruns.views.order_case', args=[nonexisting_run_pk])
        response = self.client.get(url)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)

    def test_prompt_if_no_case_run_is_passed(self):
        url = reverse('tcms.testruns.views.order_case', args=[self.test_run.pk])
        response = self.client.get(url)
        self.assertIn('At least one case is required by re-oder in run', response.content)

    def test_order_case_runs(self):
        url = reverse('tcms.testruns.views.order_case', args=[self.test_run.pk])
        response = self.client.get(url, {'case_run': [self.case_run_1.pk,
                                                      self.case_run_2.pk,
                                                      self.case_run_3.pk]})

        redirect_to = reverse('tcms.testruns.views.get', args=[self.test_run.pk])
        self.assertRedirects(response, redirect_to)

        test_sortkeys = [
            TestCaseRun.objects.get(pk=self.case_run_1.pk).sortkey,
            TestCaseRun.objects.get(pk=self.case_run_2.pk).sortkey,
            TestCaseRun.objects.get(pk=self.case_run_3.pk).sortkey,
        ]
        self.assertEqual([10, 20, 30], test_sortkeys)


class TestGetRun(BaseCaseRun):
    """Test get view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetRun, cls).setUpTestData()

    def test_404_if_non_existing_pk(self):
        url = reverse('tcms.testruns.views.get', args=[99999999])
        response = self.client.get(url)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)

    def test_get_a_run(self):
        url = reverse('tcms.testruns.views.get', args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(http_client.OK, response.status_code)

        for case_run in (self.case_run_1, self.case_run_2, self.case_run_3):
            self.assertContains(
                response,
                '<a href="#caserun_{0}">#{0}</a>'.format(case_run.pk),
                html=True)
            self.assertContains(
                response,
                '<a id="link_{0}" href="#caserun_{0}" title="Expand test case">'
                '{1}</a>'.format(case_run.pk, case_run.case.summary),
                html=True)


# ### Test cases for data ###


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

        cls.status_idle = TestCaseRunStatus.objects.get(name='IDLE')
        cls.status_failed = TestCaseRunStatus.objects.get(name='FAILED')
        cls.status_waived = TestCaseRunStatus.objects.get(name='WAIVED')

        cls.test_run = TestRunFactory(product_version=cls.version, plan=cls.plan,
                                      manager=cls.tester, default_tester=cls.tester)

        # Add extra cases for creating case runs
        cls.case_4, cls.case_5, cls.case_6 = [
            TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                            plan=[cls.plan])
            for i in range(3)]

        for case, status in ((cls.case_1, cls.status_idle),
                             (cls.case_2, cls.status_failed),
                             (cls.case_3, cls.status_failed),
                             (cls.case_4, cls.status_waived),
                             (cls.case_5, cls.status_waived),
                             (cls.case_6, cls.status_waived)):
            TestCaseRunFactory(assignee=cls.tester, tested_by=cls.tester,
                               run=cls.test_run, case=case, case_run_status=status)

    def test_get_stats(self):
        data = stats_caseruns_status(self.test_run.pk, self.case_run_statuss)

        subtotal = dict((status.pk, [0, status])
                        for status in self.case_run_statuss)
        subtotal[self.status_idle.pk][0] = 1
        subtotal[self.status_failed.pk][0] = 2
        subtotal[self.status_waived.pk][0] = 3

        expected_completed_percentage = 5.0 * 100 / 6
        expected_failure_percentage = 2.0 * 100 / 5

        self.assertEqual(subtotal, data.StatusSubtotal)
        self.assertEqual(6, data.CaseRunsTotalCount)
        self.assertEqual(expected_completed_percentage, data.CompletedPercentage)
        self.assertEqual(expected_failure_percentage, data.FailurePercentage)
