# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.tests import LoggedInTestCase
from tcms.utils.permissions import initiate_user_with_default_setups
from tcms.tests.factories import TestRunFactory, UserFactory
from tcms.testruns.models import TestRun


class TestTestRunAdmin(LoggedInTestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_run = TestRunFactory()

        cls.superuser = UserFactory()
        cls.superuser.is_superuser = True
        cls.superuser.set_password('password')
        cls.superuser.save()

    def test_regular_user_can_not_add_testrun(self):
        response = self.client.get(reverse('admin:testruns_testrun_add'))
        self.assertRedirects(response, reverse('admin:testruns_testrun_changelist'))

    def test_regular_user_can_not_change_testrun(self):
        response = self.client.get(reverse('admin:testruns_testrun_change',
                                           args=[self.test_run.pk]))
        self.assertRedirects(response, reverse('testruns-get', args=[self.test_run.pk]))

    def test_regular_user_can_not_delete_testrun(self):
        response = self.client.get(reverse('admin:testruns_testrun_delete',
                                           args=[self.test_run.pk]), follow=True)
        self.assertContains(response, _('Permission denied: TestRun does not belong to you'))

    def test_superuser_can_delete_testrun(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.superuser.username,
            password='password')
        response = self.client.get(reverse('admin:testruns_testrun_delete',
                                           args=[self.test_run.pk]))
        self.assertContains(response, _("Yes, I'm sure"))
        response = self.client.post(reverse('admin:testruns_testrun_delete',
                                            args=[self.test_run.pk]), {'post': 'yes'}, follow=True)
        self.assertRedirects(response, reverse('admin:testruns_testrun_changelist'))
        self.assertEqual(TestRun.objects.filter(pk=self.test_run.pk).exists(), False)
