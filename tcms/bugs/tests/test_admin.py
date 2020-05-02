from django.urls import reverse

from tcms.tests import LoggedInTestCase
from tcms.tests.factories import BugFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestBugAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_bug = BugFactory()

    def test_add_view_redirects_to_new_bug_view(self):
        response = self.client.get(reverse('admin:bugs_bug_add'))
        self.assertRedirects(response, reverse('bugs-new'))

    def test_change_view_redirects_to_get_bug_view(self):
        response = self.client.get(reverse('admin:bugs_bug_change',
                                           args=[self.test_bug.pk]))
        self.assertRedirects(response, reverse('bugs-get', args=[self.test_bug.pk]))
