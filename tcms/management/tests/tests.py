# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.management.models import Product, Version
from tcms.testplans.models import TestPlan, TestPlanEmailSettings
from tcms.tests.factories import (PlanTypeFactory, ProductFactory, UserFactory,
                                  VersionFactory)


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

        previous_plans_count = TestPlan.objects.count()
        TestPlan.objects.create(
            name='Test plan for the new product',
            author=self.user,
            product=product,
            product_version=product_version,
            type=plan_type,
        )
        # verify TP was created
        self.assertEqual(previous_plans_count + 1, TestPlan.objects.count())

        # make sure there are no email settings
        TestPlanEmailSettings.objects.all().delete()

        # now delete the product
        admin_delete_url = "admin:%s_%s_delete" % (
            product._meta.app_label,  # pylint: disable=no-member
            product._meta.model_name  # pylint: disable=no-member
        )
        location = reverse(admin_delete_url, args=[product.pk])
        response = self.c.get(location)
        self.assertContains(response, product.name)
        self.assertContains(response, _("Yes, I'm sure"))

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
