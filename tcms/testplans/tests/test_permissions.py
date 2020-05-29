# pylint: disable=invalid-name, too-many-ancestors

from django.urls import reverse

from tcms.tests import PermissionsTestCase, factories
from tcms.tests.factories import TestCaseFactory
from tcms.testcases.models import TestCasePlan


class ReorderCasesViewTestCase(PermissionsTestCase):
    """Test case for sorting cases"""
    permission_label = 'testplans.change_testplan'
    http_method_names = ['post']

    @classmethod
    def setUpTestData(cls):
        cls.plan = factories.TestPlanFactory()
        cls.case_1 = TestCaseFactory(
            plan=[cls.plan])
        cls.case_2 = TestCaseFactory(
            plan=[cls.plan])

        cls.post_data = {'case': [cls.case_2.pk, cls.case_1.pk]}
        cls.url = reverse('plan-reorder-cases', args=[cls.plan.pk])

        super().setUpTestData()

    def verify_post_with_permission(self):
        case1 = TestCasePlan.objects.get(plan=self.plan, case=self.case_1)
        case2 = TestCasePlan.objects.get(plan=self.plan, case=self.case_2)
        self.assertGreater(case2.sortkey, case1.sortkey)

        response = self.client.post(self.url, self.post_data)
        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})

        # Post changes the order of cases
        case1.refresh_from_db()
        case2.refresh_from_db()
        self.assertGreater(case1.sortkey, case2.sortkey)
