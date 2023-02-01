from http import HTTPStatus

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from uuslug import slugify

from tcms.testplans.models import TestPlan
from tcms.tests import LoggedInTestCase, PermissionsTestCase, user_should_have_perm
from tcms.tests.factories import (
    PlanTypeFactory,
    ProductFactory,
    TestPlanFactory,
    VersionFactory,
)


class TestNewTestPlanView(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plan_name = "TestNewTestPlanView"
        cls.product = ProductFactory()
        cls.product_version = VersionFactory(product=cls.product)
        cls.plan_type = PlanTypeFactory()
        cls.test_plan = TestPlanFactory()

        user_should_have_perm(cls.tester, perm="testplans.add_testplan")
        user_should_have_perm(cls.tester, perm="testplans.view_testplan")

        cls.location = reverse("plans-new")

        cls.request = {
            "author": cls.tester.pk,
            "product": cls.product.pk,
            "product_version": cls.product_version.pk,
            "type": cls.plan_type.pk,
            "name": cls.plan_name,
            "email_settings-0-auto_to_plan_author": "on",
            "email_settings-0-auto_to_case_owner": "on",
            "email_settings-0-auto_to_case_default_tester": "on",
            "email_settings-0-notify_on_case_update": "on",
            "email_settings-0-notify_on_plan_update": "on",
            "email_settings-0-id": cls.test_plan.emailing.pk,
            "email_settings-TOTAL_FORMS": "1",
            "email_settings-INITIAL_FORMS": "1",
            "email_settings-MIN_NUM_FORMS": "0",
            "email_settings-MAX_NUM_FORMS": "1",
            "is_active": True,
        }

    def test_plan_new_get(self):
        response = self.client.get(self.location)

        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="is_active" type="checkbox" checked',
            html=False,
        )
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_plan_author" '
            'type="checkbox" checked',
            html=False,
        )
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_owner" '
            'type="checkbox" checked',
            html=False,
        )
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_default_tester" '
            'type="checkbox" checked',
            html=False,
        )
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-notify_on_plan_update" '
            'type="checkbox" checked',
            html=False,
        )
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-notify_on_case_update" '
            'type="checkbox" checked',
            html=False,
        )

    def test_notify_formset_invalid(self):
        # Note: Boolean fields are always valid - either False or True
        # That's why the only way to make the notify formset invalid is to
        # reference a non-existing email_settings ID !!!
        data = self.request.copy()
        data["email_settings-0-id"] = -1
        del data["email_settings-0-auto_to_plan_author"]

        response = self.client.post(self.location, data)

        self.assertContains(response, _("Create new TestPlan"))
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_plan_author" '
            'type="checkbox"',
            html=False,
        )

    def test_plan_create_new_active(self):
        self._test_plan_create_new(is_active=True)

    def test_plan_create_new_inactive(self):
        self._test_plan_create_new(is_active=False)

    def _test_plan_create_new(self, is_active):
        self.request["is_active"] = is_active

        response = self.client.post(self.location, self.request)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

        plan = TestPlan.objects.get(
            name=self.plan_name,
            is_active=is_active,
        )
        self.assertEqual(plan.author, self.tester)
        self.assertEqual(plan.product, self.product)
        self.assertEqual(plan.product_version, self.product_version)
        self.assertEqual(plan.type, self.plan_type)
        self.assertEqual(plan.is_active, is_active)
        self.assertTrue(plan.emailing.auto_to_plan_author)
        self.assertTrue(plan.emailing.auto_to_case_owner)
        self.assertTrue(plan.emailing.auto_to_case_default_tester)
        self.assertTrue(plan.emailing.notify_on_plan_update)
        self.assertTrue(plan.emailing.notify_on_case_update)

    def test_with_invalid_product_shows_error(self):
        new_data = self.request.copy()
        new_data["product"] = -1
        del new_data["email_settings-0-auto_to_plan_author"]

        response = self.client.post(self.location, data=new_data, follow=True)

        self.assertContains(response, _("Create new TestPlan"))
        self.assertContains(
            response,
            _(
                "Select a valid choice. That choice is not one of the available choices."
            ),
        )
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_plan_author" '
            'type="checkbox"',
            html=False,
        )


class TestNewTestPlanViewPermissions(
    PermissionsTestCase
):  # pylint: disable=too-many-ancestors
    add_testplan_permission = "testplans.add_testplan"
    permission_label = add_testplan_permission
    http_method_names = ["get", "post"]
    url = reverse("plans-new")

    @classmethod
    def setUpTestData(cls):
        cls.post_data = {"description": "test"}
        super().setUpTestData()

        cls.plan_name = "TestNewTestPlanViewPermissions"
        cls.product = ProductFactory()
        cls.product_version = VersionFactory(product=cls.product)
        cls.plan_type = PlanTypeFactory()
        cls.test_plan = TestPlanFactory()

        user_should_have_perm(cls.tester, perm="testplans.view_testplan")

        cls.post_data.update(  # pylint: disable=objects-update-used
            {
                "author": cls.tester.pk,
                "product": cls.product.pk,
                "product_version": cls.product_version.pk,
                "type": cls.plan_type.pk,
                "name": cls.plan_name,
                "email_settings-0-auto_to_plan_author": "on",
                "email_settings-0-auto_to_case_owner": "on",
                "email_settings-0-auto_to_case_default_tester": "on",
                "email_settings-0-notify_on_case_update": "on",
                "email_settings-0-notify_on_plan_update": "on",
                "email_settings-0-id": cls.test_plan.emailing.pk,
                "email_settings-TOTAL_FORMS": "1",
                "email_settings-INITIAL_FORMS": "1",
                "email_settings-MIN_NUM_FORMS": "0",
                "email_settings-MAX_NUM_FORMS": "1",
                "is_active": True,
            }
        )

    def verify_get_with_permission(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("Create new TestPlan"))

    def verify_post_with_permission(self):
        response = self.client.post(self.url, self.post_data, follow=True)
        test_plan = TestPlan.objects.get(
            name=self.post_data["name"],
        )
        redirect_url = reverse(
            "test_plan_url", args=[test_plan.pk, slugify(test_plan.name)]
        )

        self.assertRedirects(response, redirect_url)
        self.assertContains(response, self.post_data["name"])
