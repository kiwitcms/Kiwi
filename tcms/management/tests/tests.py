# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from http import HTTPStatus

from django.test import TestCase
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from tcms.management.models import Product, Version
from tcms.testplans.models import TestPlan
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import PlanTypeFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class ProductTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username='admin', email='admin@example.com')
        cls.user.set_password('admin')  # nosec:B106:hardcoded_password_funcarg
        cls.user.is_superuser = True
        cls.user.is_staff = True  # enables access to admin panel
        cls.user.save()

        cls.c = Client()
        cls.c.login(username='admin', password='admin')  # nosec:B106:hardcoded_password_funcarg

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
        """
        # setup
        product = ProductFactory(name='Something to delete')
        product_version = VersionFactory(value='0.1', product=product)
        plan_type = PlanTypeFactory()

        # create Test Plan via the UI by sending a POST request to the view
        previous_plans_count = TestPlan.objects.count()
        test_plan_name = 'Test plan for the new product'
        response = self.c.post(reverse('plans-new'), {
            'name': test_plan_name,
            'product': product.pk,
            'product_version': product_version.pk,
            'type': plan_type.pk,
        }, follow=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        # verify test plan was created
        self.assertTrue(test_plan_name in str(response.content,
                                              encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(previous_plans_count + 1, TestPlan.objects.count())

        # now delete the product
        admin_delete_url = "admin:%s_%s_delete" % (
            product._meta.app_label,  # pylint: disable=no-member
            product._meta.model_name  # pylint: disable=no-member
        )
        location = reverse(admin_delete_url, args=[product.pk])
        response = self.c.get(location)
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertTrue('Are you sure you want to delete the product "%s"' % product.name
                        in str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertTrue("Yes, I'm sure" in str(response.content,
                                               encoding=settings.DEFAULT_CHARSET))

        # confirm that we're sure we want to delete it
        response = self.c.post(location, {'post': 'yes'})
        self.assertEqual(302, response.status_code)
        self.assertTrue('/admin/%s/%s/' % (
            product._meta.app_label, product._meta.model_name)  # pylint: disable=no-member
                        in response['Location'])

        # verify everything has been deleted
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertFalse(Version.objects.filter(pk=product_version.pk).exists())
        self.assertEqual(previous_plans_count, TestPlan.objects.count())
