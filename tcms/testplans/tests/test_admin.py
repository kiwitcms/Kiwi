from django.urls import reverse
from tcms.tests import LoggedInTestCase
from tcms.utils.permissions import initiate_user_with_default_setups
from tcms.tests.factories import TestPlanFactory


class TestTestPlanAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_plan = TestPlanFactory()

    def test_users_can_not_add_testplan(self):
        response = self.client.get(reverse('admin:testplans_testplan_add'))
        self.assertRedirects(response, reverse('admin:testplans_testplan_changelist'))

    def test_users_can_not_change_testplan(self):
        response = self.client.get(reverse('admin:testplans_testplan_change',
                                           args=[self.test_plan.pk]))
        self.assertRedirects(response, reverse('test_plan_url_short', args=[self.test_plan.pk]),
                             target_status_code=301)
