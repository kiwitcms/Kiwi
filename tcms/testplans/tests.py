# -*- coding: utf-8 -*-

import httplib
import os
import xml.etree.ElementTree as et

from django import test
from django.core.urlresolvers import reverse
from django.test.client import Client

from tcms.settings.common import TCMS_ROOT_PATH
from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testplans.models import TestPlan
from tcms.tests.factories import ClassificationFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class PlanTests(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')
        cls.user.is_superuser = True
        cls.user.save()

        cls.c = Client()
        cls.c.login(username='admin', password='admin')

        cls.classification = ClassificationFactory(name='Auto')
        cls.product = ProductFactory(name='Nitrate', classification=cls.classification)
        cls.product_version = VersionFactory(value='0.1', product=cls.product)
        cls.plan_type = TestPlanTypeFactory()

        cls.test_plan = TestPlanFactory(name='another test plan for testing',
                                        product_version=cls.product_version,
                                        owner=cls.user,
                                        author=cls.user,
                                        product=cls.product,
                                        type=cls.plan_type)
        cls.plan_id = cls.test_plan.pk

    def test_open_plans_search(self):
        location = reverse('tcms.testplans.views.all')
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_search_plans(self):
        location = reverse('tcms.testplans.views.all')
        response = self.c.get(location, {'action': 'search', 'type': self.test_plan.type.pk})
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_new_get(self):
        location = reverse('tcms.testplans.views.new')
        response = self.c.get(location, follow=True)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_clone(self):
        location = reverse('tcms.testplans.views.clone')
        response = self.c.get(location, {'plan_id': self.plan_id})
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_details(self):
        location = reverse('tcms.testplans.views.get', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.MOVED_PERMANENTLY)

        response = self.c.get(location, follow=True)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_cases(self):
        location = reverse('tcms.testplans.views.cases', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_importcase(self):
        location = reverse('tcms.testplans.views.cases', args=[self.plan_id])
        filename = os.path.join(TCMS_ROOT_PATH, 'fixtures', 'cases-to-import.xml')
        with open(filename, 'r') as fin:
            response = self.c.post(location, {'a': 'import_cases', 'xml_file': fin}, follow=True)
        self.assertEquals(response.status_code, httplib.OK)

        summary = 'Remove this case from a test plan'
        has_case = TestCase.objects.filter(summary=summary).exists()
        self.assertTrue(has_case)

    def test_plan_delete(self):
        tp_pk = self.test_plan.pk

        location = reverse('tcms.testplans.views.delete', args=[tp_pk])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

        response = self.c.get(location, {'sure': 'no'})
        self.assertEquals(response.status_code, httplib.OK)

        response = self.c.get(location, {'sure': 'yes'})
        self.assertEquals(response.status_code, httplib.OK)
        deleted = not TestPlan.objects.filter(pk=tp_pk).exists()
        self.assert_(deleted,
                     'TestPlan {0} should be deleted. But, not.'.format(tp_pk))

    def test_plan_edit(self):
        location = reverse('tcms.testplans.views.edit', args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_printable_without_selected_plan(self):
        location = reverse('tcms.testplans.views.printable')
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)
        self.assertEqual(response.context['info'], 'At least one target is required.')

    def test_plan_printable(self):
        location = reverse('tcms.testplans.views.printable')
        response = self.c.get(location, {'plan': self.plan_id})
        self.assertEquals(response.status_code, httplib.OK)

        for test_plan in response.context['test_plans']:
            self.assertTrue(test_plan.pk > 0)
            self.assertTrue(test_plan.name is not '')
            self.assertTrue(test_plan.summary is not '')
            self.assertTrue(test_plan.latest_text.plan_text is not '')

            self.assertTrue(len(test_plan.result_set) > 0)
            for case in test_plan.result_set:
                self.assertTrue(case.case_id > 0)
                self.assertTrue(case.summary is not '')
                # factory sets all 4
                self.assertTrue(case.setup is not '')
                self.assertTrue(case.action is not '')
                self.assertTrue(case.effect is not '')
                self.assertTrue(case.breakdown is not '')

    def test_plan_export(self):
        location = reverse('tcms.testplans.views.export')
        response = self.c.get(location, {'plan': self.plan_id})
        self.assertEquals(response.status_code, httplib.OK)

        xml_doc = response.content
        try:
            et.fromstring(xml_doc)
        except et.ParseError:
            self.fail('XML document exported from test plan is invalid.')

    def test_plan_attachment(self):
        location = reverse('tcms.testplans.views.attachment',
                           args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

    def test_plan_history(self):
        location = reverse('tcms.testplans.views.text_history',
                           args=[self.plan_id])
        response = self.c.get(location)
        self.assertEquals(response.status_code, httplib.OK)

        response = self.c.get(location, {'plan_text_version': 1})
        self.assertEquals(response.status_code, httplib.OK)


class TestPlanModel(test.TestCase):
    """ Test some model operations directly without a view """

    @classmethod
    def setUpTestData(cls):
        cls.plan_1 = TestPlanFactory()
        cls.testcase_1 = TestCaseFactory()
        cls.testcase_2 = TestCaseFactory()

        cls.plan_1.add_case(cls.testcase_1)
        cls.plan_1.add_case(cls.testcase_2)

    def test_plan_delete(self):
        self.plan_1.delete_case(self.testcase_1)
        cases_left = TestCasePlan.objects.filter(plan=self.plan_1.pk)
        self.assertEqual(1, cases_left.count())
        self.assertEqual(self.testcase_2.pk, cases_left[0].case.pk)
