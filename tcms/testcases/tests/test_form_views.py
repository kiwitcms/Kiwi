# -*- coding: utf-8 -*-

from django import test
from django.urls import reverse
from django.conf import settings

from tcms.testcases.forms import CaseAutomatedForm
from tcms.tests.factories import UserFactory


class TestForm_AutomatedView(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tester = UserFactory()
        cls.tester.set_password('password')
        cls.tester.save()

    def setUp(self):
        super().setUp()
        self.client.login(username=self.tester.username,  # nosec:B106:hardcoded_password_funcarg
                          password='password')

    def test_get_form(self):
        """Verify the view renders the expected HTML"""
        response = self.client.get(reverse('testcases-form-automated'))
        form = CaseAutomatedForm()
        self.assertHTMLEqual(str(response.content, encoding=settings.DEFAULT_CHARSET), form.as_p())
