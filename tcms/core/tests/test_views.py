# -*- coding: utf-8 -*-

from six.moves import http_client

from django.core.urlresolvers import reverse

from tcms.tests import BasePlanCase
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestCaseRunFactory


class TestQuickSearch(BasePlanCase):

    @classmethod
    def setUpTestData(cls):
        super(TestQuickSearch, cls).setUpTestData()

        cls.test_run = TestRunFactory(plan=cls.plan)
        cls.case_run_1 = TestCaseRunFactory(case=cls.case_1, run=cls.test_run)
        cls.case_run_2 = TestCaseRunFactory(case=cls.case_2, run=cls.test_run)
        cls.case_run_3 = TestCaseRunFactory(case=cls.case_3, run=cls.test_run)

        cls.search_url = reverse('tcms.core.views.search')

    def test_goto_plan(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'plans', 'search_content': self.plan.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testplans.views.get', args=[self.plan.pk]),
            target_status_code=http_client.MOVED_PERMANENTLY)

    def test_goto_case(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'cases', 'search_content': self.case_1.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testcases.views.get', args=[self.case_1.pk]))

    def test_goto_run(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'runs', 'search_content': self.test_run.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testruns.views.get', args=[self.test_run.pk]))

    def test_goto_plan_search(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'plans', 'search_content': 'keyword'})
        url = '{}?a=search&search=keyword'.format(reverse('tcms.testplans.views.all'))
        self.assertRedirects(response, url)

    def test_goto_case_search(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'cases', 'search_content': 'keyword'})
        url = '{}?a=search&search=keyword'.format(reverse('tcms.testcases.views.all'))
        self.assertRedirects(response, url)

    def test_goto_run_search(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'runs', 'search_content': 'keyword'})
        url = '{}?a=search&search=keyword'.format(reverse('tcms.testruns.views.all'))
        self.assertRedirects(response, url)
