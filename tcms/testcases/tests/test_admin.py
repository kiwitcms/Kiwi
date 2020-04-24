from django.urls import reverse

from tcms.tests import LoggedInTestCase
from tcms.tests.factories import TestCaseFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestTestCaseAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_case = TestCaseFactory()

    def test_add_view_always_redirects_to_new_case_view(self):
        response = self.client.get(reverse('admin:testcases_testcase_add'))
        self.assertRedirects(response, reverse('testcases-new'))

    def test_change_view_redirects_to_testcase_get_view(self):
        response = self.client.get(reverse('admin:testcases_testcase_change',
                                           args=[self.test_case.pk]))
        self.assertRedirects(response, reverse('testcases-get', args=[self.test_case.pk]))
