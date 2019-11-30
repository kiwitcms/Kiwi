# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import json

from django.conf import settings
from django.urls import reverse


from tcms.tests import PermissionsTestCase, factories
from tcms.tests.factories import TestCaseFactory
from tcms.testcases.models import TestCasePlan


class DeleteCasesViewTestCase(PermissionsTestCase):
    """Test case for deleting cases from a plan"""

    permission_label = 'testplans.change_testplan'
    http_method_names = ['post']

    @classmethod
    def setUpTestData(cls):
        cls.plan = factories.TestPlanFactory()
        cls.url = reverse('plan-delete-cases', args=[cls.plan.pk])

        cls.case_1 = TestCaseFactory(
            plan=[cls.plan])
        cls.case_2 = TestCaseFactory(
            plan=[cls.plan])
        cls.case_3 = TestCaseFactory(
            plan=[cls.plan])
        cls.post_data['case'] = [cls.case_1.pk, cls.case_3.pk]
        super().setUpTestData()

    def verify_post_with_permission(self):
        self.assertTrue(self.plan.case.filter(
            pk__in=[self.case_1.pk, self.case_2.pk, self.case_3.pk]).exists())

        response = self.client.post(self.url, self.post_data)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(0, data['rc'])
        self.assertEqual('ok', data['response'])
        self.assertFalse(self.plan.case.filter(
            pk__in=[self.case_1.pk, self.case_3.pk]).exists())
        self.assertTrue(self.plan.case.filter(
            pk__in=[self.case_2.pk]).exists())


class ReorderCasesViewTestCase(PermissionsTestCase):
    """Test case for sorting cases"""
    permission_label = 'testplans.change_testplan'
    http_method_names = ['post']

    @classmethod
    def setUpTestData(cls):
        cls.plan = factories.TestPlanFactory()
        cls.case_1 = TestCaseFactory(
            plan=[cls.plan])
        cls.case_3 = TestCaseFactory(
            plan=[cls.plan])

        cls.post_data = {'case': [cls.case_3.pk, cls.case_1.pk]}
        cls.url = reverse('plan-reorder-cases', args=[cls.plan.pk])

        super().setUpTestData()

    def verify_post_with_permission(self):

        response = self.client.post(self.url, self.post_data)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual({'rc': 0, 'response': 'ok'}, data)

        case_plan_rel = TestCasePlan.objects.get(plan=self.plan, case=self.case_3)
        self.assertEqual(10, case_plan_rel.sortkey)

        case_plan_rel = TestCasePlan.objects.get(plan=self.plan, case=self.case_1)
        self.assertEqual(20, case_plan_rel.sortkey)
