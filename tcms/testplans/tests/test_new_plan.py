from http import HTTPStatus

from django.urls import reverse

from tcms.testplans.models import TestPlan
from tcms.testplans.tests.tests import BasePlanTest
from tcms.tests import remove_perm_from_user, user_should_have_perm


class NewPlanViewTest(BasePlanTest):
    location = reverse('plans-new')
    plan_name = 'plan name'
    add_testplan_permission = 'testplans.add_testplan'

    def setUp(self):
        super().setUp()

        user_should_have_perm(self.user, perm=self.add_testplan_permission)

        self.user.is_superuser = False
        self.user.save()

        self.request = {
            'author': self.user.pk,
            'product': self.product.pk,
            'product_version': self.product_version.pk,
            'type': self.plan_type.pk,
            'name': self.plan_name,

            'email_settings-0-auto_to_plan_author': 'on',
            'email_settings-0-auto_to_case_owner': 'on',
            'email_settings-0-auto_to_case_default_tester': 'on',
            'email_settings-0-notify_on_case_update': 'on',
            'email_settings-0-notify_on_plan_update': 'on',

            'email_settings-0-plan': '',
            'email_settings-0-id': self.test_plan.emailing.pk,
            'email_settings-TOTAL_FORMS': '1',
            'email_settings-INITIAL_FORMS': '1',
            'email_settings-MIN_NUM_FORMS': '0',
            'email_settings-MAX_NUM_FORMS': '1',
        }

    def test_plan_new_get(self):
        response = self.client.get(self.location)

        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="is_active" type="checkbox" checked>',
            html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_plan_author" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_owner" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_default_tester" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-notify_on_plan_update" '
            'type="checkbox" checked>', html=True)
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-notify_on_case_update" '
            'type="checkbox" checked>', html=True)

    def test_plan_create_new_active(self):
        self._test_plan_create_new(is_active=True)

    def test_plan_create_new_inactive(self):
        self._test_plan_create_new(is_active=False)

    def _test_plan_create_new(self, is_active):
        self.request['is_active'] = is_active

        response = self.client.post(self.location, self.request)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        plan = TestPlan.objects.get(
            name=self.plan_name,
            is_active=is_active,
        )
        self.assertEqual(plan.author, self.user)
        self.assertEqual(plan.product, self.product)
        self.assertEqual(plan.product_version, self.product_version)
        self.assertEqual(plan.type, self.plan_type)
        self.assertEqual(plan.is_active, is_active)
        self.assertTrue(plan.emailing.auto_to_plan_author)
        self.assertTrue(plan.emailing.auto_to_case_owner)
        self.assertTrue(plan.emailing.auto_to_case_default_tester)
        self.assertTrue(plan.emailing.notify_on_plan_update)
        self.assertTrue(plan.emailing.notify_on_case_update)

    def test_get_with_no_perm_redirects_to_login(self):
        remove_perm_from_user(self.user, self.add_testplan_permission)

        response = self.client.get(self.location, follow=True)

        self.assertRedirects(response, reverse('tcms-login') + '?next=' + self.location)

    def test_post_with_no_perm_redirects_to_login(self):
        remove_perm_from_user(self.user, self.add_testplan_permission)

        response = self.client.post(self.location, self.request, follow=True)

        self.assertRedirects(response, reverse('tcms-login') + '?next=' + self.location)
