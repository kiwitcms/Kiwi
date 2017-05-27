# -*- coding: utf-8 -*-

from six.moves import http_client

from django import test
from django.core.urlresolvers import reverse

from tcms.testruns.models import TestRun
from tcms.testruns.models import TestCaseRun
from tcms.tests import BaseCaseRun


# ### Test case for View methods ###


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
