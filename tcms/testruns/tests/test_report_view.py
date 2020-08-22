# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

from http import HTTPStatus

from django.urls import reverse

from tcms.tests import BaseCaseRun
from tcms.tests import user_should_have_perm
from tcms.tests.factories import LinkReferenceFactory


class Test_TestRunReport(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, 'testruns.view_testrun')

        cls.bug_1 = LinkReferenceFactory(execution=cls.execution_1)
        cls.bug_2 = LinkReferenceFactory(execution=cls.execution_2)
        cls.bug_3 = LinkReferenceFactory(execution=cls.execution_3)

    def test_reports(self):
        url = reverse('run-report', args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.bug_1.url)
        self.assertContains(response, self.bug_2.url)
        self.assertContains(response, self.bug_3.url)
