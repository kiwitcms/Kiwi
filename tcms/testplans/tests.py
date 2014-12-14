# -*- coding: utf-8 -*-

import httplib
import os
import xml.etree.ElementTree as et

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from django import test

from tcms.settings.common import TCMS_ROOT_PATH
from tcms.management.models import Classification
from tcms.management.models import Product
from tcms.management.models import Version
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.testplans.models import TestPlanType


class PlanTests(test.TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin',
                                                  email='admin@example.com',
                                                  password='admin')
        self.c = Client()
        self.c.post('/accounts/login/',
                    {'username': 'admin', 'password': 'admin'},
                    follow=True)

        self.classification = Classification.objects.create(name='Auto')
        self.product = Product.objects.create(name='Nitrate', classification=self.classification)
        self.product_version = Version.objects.create(value='0.1', product=self.product)
        self.plan_type = TestPlanType.objects.all()[0]

        self.test_plan = TestPlan.objects.create(name='another test plan for testing',
                                                 product_version=self.product_version,
                                                 author=self.user,
                                                 product=self.product,
                                                 type=self.plan_type)
        self.plan_id = self.test_plan.pk

    def tearDown(self):
        self.test_plan.delete()
        self.product_version.delete()
        self.product.delete()
        self.classification.delete()

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
        filename = os.path.join(TCMS_ROOT_PATH,
                                'fixtures', 'cases-to-import.xml')
        with open(filename, 'r') as fin:
            response = self.c.post(location, {'a': 'import_cases',
                                              'xml_file': fin}, follow=True)
        self.assertEquals(response.status_code, httplib.OK)

        summary = 'Remove this case from a test plan'
        has_case = TestCase.objects.filter(summary=summary).exists()
        self.assert_(has_case)

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

    def test_plan_printable(self):
        location = reverse('tcms.testplans.views.printable')
        response = self.c.get(location, {'plan_id': self.plan_id})
        self.assertEquals(response.status_code, httplib.OK)

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
