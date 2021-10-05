from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.testplans.models import TestPlan
from tcms.tests import LoggedInTestCase
from tcms.tests.factories import TestPlanFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestTestPlanAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_plan = TestPlanFactory()

    def test_users_can_add_testplan_via_customized_page(self):
        response = self.client.get(reverse("admin:testplans_testplan_add"))
        self.assertRedirects(response, reverse("plans-new"))

    def test_users_can_not_change_testplan(self):
        response = self.client.get(
            reverse("admin:testplans_testplan_change", args=[self.test_plan.pk])
        )
        self.assertRedirects(
            response,
            reverse("test_plan_url_short", args=[self.test_plan.pk]),
            target_status_code=301,
        )

    def test_users_can_delete_testplan(self):
        response = self.client.get(
            reverse("admin:testplans_testplan_delete", args=[self.test_plan.pk])
        )
        self.assertContains(response, _("Yes, I'm sure"))
        response = self.client.post(
            reverse("admin:testplans_testplan_delete", args=[self.test_plan.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertRedirects(response, reverse("core-views-index"))
        self.assertEqual(TestPlan.objects.filter(pk=self.test_plan.pk).exists(), False)

    def test_history_display_testplan(self):
        with self.subTest("Test History before Changes"):
            response = self.client.get(
                f"/admin/testplans/testplan/{self.test_plan.pk}/history/"
            )
            self.assertContains(response, "<pre></pre>")
            self.assertContains(response, _("Created"))

        old_test_plan_name = self.test_plan.name
        old_test_plan_url = self.test_plan.get_absolute_url()

        with self.subTest("Test changes included in history"):
            self.test_plan.name = "Test Demo"
            self.test_plan.save()
            response = self.client.get(
                f"/admin/testplans/testplan/{self.test_plan.pk}/history/"
            )
            self.assertContains(
                response,
                f"<pre>--- name\n+++ name\n@@ -1 +1 @@\n-{old_test_plan_name}\n+Test Demo</pre>",
            )

        with self.subTest("Test fields are read-only"):
            response = self.client.get(
                f"/admin/testplans/testplan/{self.test_plan.pk}/"
                f"history/{self.test_plan.history.last().pk}/"
            )
            self.assertNotContains(
                response,
                '<input type="text"',
            )

        with self.subTest("Test Reverting Redirect to Object"):
            response = self.client.post(
                f"/admin/testplans/testplan/{self.test_plan.pk}/"
                f"history/{self.test_plan.history.last().pk}/",
                follow=True,
            )
            self.assertRedirects(
                response,
                old_test_plan_url,
            )
