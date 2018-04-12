# -*- coding: utf-8 -*-

from django import test
from django.urls import reverse
from django.conf import settings

from tcms.testcases.forms import CaseAutomatedForm


class TestForm_AutomatedView(test.TestCase):
    def test_get_form(self):
        """Verify the view renders the expected HTML"""
        response = self.client.get(reverse('testcases-form-automated'))
        form = CaseAutomatedForm()
        self.assertHTMLEqual(str(response.content, encoding=settings.DEFAULT_CHARSET), form.as_p())
