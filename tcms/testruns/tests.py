# -*- coding: utf-8 -*-

import httplib

from django import test
from django.core.urlresolvers import reverse

from tcms.testcases.models import TestCaseBugSystem
from tcms.testruns.models import TestRun
from tcms.testruns.models import TestCaseRun
from tcms.tests import BaseCaseRun
from tcms.tests.factories import TestRunFactory


# ### Test cases for models ###


class TestRunGetBugsCount(BaseCaseRun):
    """Test TestRun.get_bug_count"""

    @classmethod
    def setUpTestData(cls):
        super(TestRunGetBugsCount, cls).setUpTestData()

        bug_tracker = TestCaseBugSystem.objects.first()
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


# ### Test cases for View methods ###


class TestOrderCases(BaseCaseRun):
    """Test view method order_case"""

    @classmethod
    def setUpTestData(cls):
        super(TestOrderCases, cls).setUpTestData()

        cls.client = test.Client()

    def test_404_if_run_does_not_exist(self):
        nonexisting_run_pk = TestRun.objects.last().pk + 1
        url = reverse('testruns-order_case', args=[nonexisting_run_pk])
        response = self.client.get(url)
        self.assertEqual(httplib.NOT_FOUND, response.status_code)

    def test_prompt_if_no_case_run_is_passed(self):
        url = reverse('testruns-order_case', args=[self.test_run.pk])
        response = self.client.get(url)
        self.assertIn('At least one case is required by re-oder in run', response.content)

    def test_order_case_runs(self):
        url = reverse('testruns-order_case', args=[self.test_run.pk])
        response = self.client.get(url, {'case_run': [self.case_run_1.pk,
                                                      self.case_run_2.pk,
                                                      self.case_run_3.pk]})

        redirect_to = reverse('testruns-get', args=[self.test_run.pk])
        self.assertRedirects(response, redirect_to)

        test_sortkeys = [
            TestCaseRun.objects.get(pk=self.case_run_1.pk).sortkey,
            TestCaseRun.objects.get(pk=self.case_run_2.pk).sortkey,
            TestCaseRun.objects.get(pk=self.case_run_3.pk).sortkey,
        ]
        self.assertEqual([10, 20, 30], test_sortkeys)
