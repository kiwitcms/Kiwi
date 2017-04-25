# -*- coding: utf-8 -*-

import httplib

from django import test
from django.core.urlresolvers import reverse
from django.test.client import Client

from tcms.management.models import Product, Version
from tcms.testplans.models import TestPlan, _listen, _disconnect_signals
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TestPlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class ProductTests(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')
        cls.user.is_superuser = True
        cls.user.is_staff = True  # enables access to admin panel
        cls.user.save()

        cls.c = Client()
        cls.c.login(username='admin', password='admin')

    def test_product_delete_with_test_plan_wo_email_settings(self):
        """
            A test to demonstrate Issue #181.

            Steps to reproduce:
            1) Create a new Product
            2) Create a new Test Plan for Product
            3) DON'T edit the Test Plan
            4) Delete the Product

            Expected results:
            0) No errors
            1) Product is deleted
            2) Test Plan is deleted

            NOTE: we manually connect signals handlers here
            b/c in est mode LISTENING_MODEL_SIGNAL = False
        """
        # connect signal handlers
        _listen()

        try:
            # setup
            product = ProductFactory(name='Something to delete')
            product_version = VersionFactory(value='0.1', product=product)
            plan_type = TestPlanTypeFactory()

            # create Test Plan via the UI by sending a POST request to the view
            previous_plans_count = TestPlan.objects.count()
            test_plan_name = 'Test plan for the new product'
            response = self.c.post(reverse('tcms.testplans.views.new'), {
                'name': test_plan_name,
                'product': product.pk,
                'product_version': product_version.pk,
                'type': plan_type.pk,
            }, follow=True)
            self.assertEqual(httplib.OK, response.status_code)
            # verify test plan was created
            self.assertTrue(test_plan_name in response.content)
            self.assertEqual(previous_plans_count + 1, TestPlan.objects.count())

            # now delete the product
            admin_delete_url = "admin:%s_%s_delete" % (product._meta.app_label, product._meta.model_name)
            location = reverse(admin_delete_url, args=[product.pk])
            response = self.c.get(location)
            self.assertEqual(httplib.OK, response.status_code)
            self.assertTrue('Are you sure you want to delete the product "%s"' % product.name in response.content)
            self.assertTrue("Yes, I'm sure" in response.content)

            # confirm that we're sure we want to delete it
            response = self.c.post(location, {'post': 'yes'})
            self.assertEqual(302, response.status_code)
            self.assertTrue('/admin/%s/%s/' % (product._meta.app_label, product._meta.model_name) in response['Location'])

            # verify everything has been deleted
            self.assertFalse(Product.objects.filter(pk=product.pk).exists())
            self.assertFalse(Version.objects.filter(pk=product_version.pk).exists())
            self.assertEqual(previous_plans_count, TestPlan.objects.count())
        finally:
            # disconnect signals to avoid influencing other tests
            _disconnect_signals()
