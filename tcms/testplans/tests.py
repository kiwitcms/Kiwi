# -*- coding: utf-8 -*-

import httplib
import os
import xml.etree.ElementTree as et

from django import test
from django.core.urlresolvers import reverse
from django.test.client import Client

from tcms.settings.common import TCMS_ROOT_PATH
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.tests.factories import ClassificationFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class PlanTests(test.TestCase):

    @classmethod
    def setUpClass(cls):
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

    @classmethod
    def tearDownClass(cls):
        cls.c.logout()
        cls.test_plan.delete()
        cls.product_version.delete()
        cls.product.delete()
        cls.classification.delete()
        cls.user.delete()

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
