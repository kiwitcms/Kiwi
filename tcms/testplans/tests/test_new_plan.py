from http import HTTPStatus

from django.urls import reverse

from tcms.testplans.models import TestPlan
from tcms.testplans.tests.tests import BasePlanTest


class NewPlanViewTest(BasePlanTest):
    location = reverse('plans-new')

    def test_plan_new_get(self):
        response = self.client.get(self.location, follow=True)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="is_active" type="checkbox" checked>',
            html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="auto_to_plan_author" type="checkbox" '
            'checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="auto_to_case_owner" type="checkbox" '
            'checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="auto_to_case_default_tester" type="checkbox" '
            'checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="notify_on_plan_update" type="checkbox" '
            'checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="notify_on_case_update" type="checkbox" '
            'checked>', html=True)

    def test_plan_create_new_active(self):
        self._test_plan_create_new(is_active=True)

    def test_plan_create_new_inactive(self):
        self._test_plan_create_new(is_active=False)

    def _test_plan_create_new(self, is_active):
        plan_name = 'plan name'
        request = {
            'product': self.product.id,
            'product_version': self.product_version.id,
            'type': self.plan_type.pk,
            'name': plan_name,
            'is_active': is_active,
            'auto_to_plan_author': True,
            'auto_to_case_owner': True,
            'auto_to_case_default_tester': True,
            'notify_on_case_update': False,
        }

        response = self.client.post(self.location, request, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        plan = TestPlan.objects.get(name=plan_name)
        self.assertEqual(plan.product, self.product)
        self.assertEqual(plan.product_version, self.product_version)
        self.assertEqual(plan.type, self.plan_type)
        self.assertEqual(plan.is_active, is_active)
        self.assertTrue(plan.emailing.auto_to_plan_author)
        self.assertTrue(plan.emailing.auto_to_case_owner)
        self.assertTrue(plan.emailing.auto_to_case_default_tester)
        self.assertFalse(plan.emailing.notify_on_plan_update)
        self.assertFalse(plan.emailing.notify_on_case_update)