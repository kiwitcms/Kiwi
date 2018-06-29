# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from http import HTTPStatus
from django.urls import reverse

from tcms.testcases.models import BugSystem

from tcms.tests import BaseCaseRun


class Test_TestRunReportUnconfiguredJIRA(BaseCaseRun):
    """
        When JIRA isn't fully configured, i.e. missing API URL
        Username and Password/Token this leads to errors when
        generating TR reports. See
        https://github.com/kiwitcms/Kiwi/issues/100

        The problem is the underlying JIRA client assumes default
        values and tries to connect to the JIRA instance upon
        object creation!
    """

    @classmethod
    def setUpTestData(cls):
        super(Test_TestRunReportUnconfiguredJIRA, cls).setUpTestData()

        # NOTE: base_url, api_url, api_username and api_password
        # are intentionally left blank!
        cls.it = BugSystem.objects.create(
            name='Partially configured JIRA',
            url_reg_exp='https://jira.example.com/browse/%s',
            validate_reg_exp=r'^[A-Z0-9]+-\d+$',
            tracker_type='JIRA'
        )

        cls.case_run_1.add_bug('KIWI-1234', cls.it.pk)

    def test_reports(self):
        url = reverse('run-report', args=[self.case_run_1.run_id])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.it.url_reg_exp % 'KIWI-1234')


class Test_TestRunReportUnconfiguredBugzilla(BaseCaseRun):
    """
        Test for https://github.com/kiwitcms/Kiwi/issues/100
    """

    @classmethod
    def setUpTestData(cls):
        super(Test_TestRunReportUnconfiguredBugzilla, cls).setUpTestData()

        # NOTE: base_url, api_url, api_username and api_password
        # are intentionally left blank!
        cls.it = BugSystem.objects.create(
            name='Partially configured Bugzilla',
            url_reg_exp='https://bugzilla.example.com/show_bug.cgi?id=%s',
            validate_reg_exp=r'^\d{1,7}$',
            tracker_type='Bugzilla'
        )

        cls.case_run_1.add_bug('5678', cls.it.pk)

    def test_reports(self):
        url = reverse('run-report', args=[self.case_run_1.run_id])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.it.url_reg_exp % '5678')


class Test_TestRunReportUnconfiguredGitHub(BaseCaseRun):
    """
        Test for https://github.com/kiwitcms/Kiwi/issues/100
    """

    @classmethod
    def setUpTestData(cls):
        super(Test_TestRunReportUnconfiguredGitHub, cls).setUpTestData()

        # NOTE: base_url, api_url, api_username and api_password
        # are intentionally left blank!
        cls.it = BugSystem.objects.create(
            name='Partially configured GitHub',
            url_reg_exp='https://github.com/kiwitcms/Kiwi/issues/%s',
            validate_reg_exp=r'^\d+$',
            tracker_type='GitHub'
        )

        cls.case_run_1.add_bug('100', cls.it.pk)

    def test_reports(self):
        url = reverse('run-report', args=[self.case_run_1.run_id])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, self.it.url_reg_exp % '100')
