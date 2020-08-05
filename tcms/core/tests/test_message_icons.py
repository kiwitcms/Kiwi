from django.urls import reverse
from tcms.core.templatetags.extra_filters import message_icon
from tcms.tests import LoggedInTestCase
from tcms.tests.factories import TestRunFactory


class TestMessageIcons(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.test_run = TestRunFactory()

    def test_error_message_icon(self):
        response = self.client.get(reverse('admin:testruns_testrun_delete',
                                           args=[self.test_run.pk]), follow=True)
        msg = list(response.context['messages'])[0]
        self.assertEqual(message_icon(msg), 'pficon-error-circle-o')
