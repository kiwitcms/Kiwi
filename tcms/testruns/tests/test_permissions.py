# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

import unittest

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms import tests
from tcms.tests import user_should_have_perm
from tcms.tests import PermissionsTestCase, factories
from tcms.testruns.models import TestRun
from tcms.testcases.models import TestCaseStatus


class EditTestRunViewTestCase(PermissionsTestCase):
    """Test permissions for TestRun edit action"""

    permission_label = 'testruns.change_testrun'
    http_method_names = ['get', 'post']

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory(summary='Old summary')
        cls.url = reverse('testruns-edit', args=[cls.test_run.pk])
        cls.new_build = factories.BuildFactory(name='FastTest', product=cls.test_run.plan.product)
        intern = factories.UserFactory(username='intern',
                                       email='intern@example.com')
        cls.post_data = {
            'summary': 'New run summary',
            'build': cls.new_build.pk,
            'manager': cls.test_run.manager.email,
            'default_tester': intern.email,
            'notes': 'New run notes',
        }
        super().setUpTestData()

    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assertContains(
            response,
            '<input type="text" id="id_summary" name="summary" value="%s" class="form-control"'
            ' required>' % self.test_run.summary,
            html=True
        )
        self.assertContains(response, '<input id="id_manager" name="manager" value="%s"'
                                      ' type="text" class="form-control" placeholder='
                                      '"%s" required>'
                            % (self.test_run.manager, _('Username or email')), html=True)
        self.assertContains(response, _('Edit TestRun'))
        self.assertContains(response, 'testruns/js/mutable.js')

    def verify_post_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.view_testrun')

        response = self.client.post(self.url, self.post_data)
        self.test_run.refresh_from_db()

        self.assertEqual(self.test_run.summary, 'New run summary')
        self.assertEqual(self.test_run.build, self.new_build)
        self.assertEqual(self.test_run.notes, 'New run notes')
        self.assertRedirects(
            response,
            reverse('testruns-get', args=[self.test_run.pk]))


class CreateTestRunViewTestCase(tests.PermissionsTestCase):
    permission_label = 'testruns.add_testrun'
    http_method_names = ['post']
    url = reverse('testruns-new')

    @classmethod
    def setUpTestData(cls):

        cls.plan = factories.TestPlanFactory()

        cls.build_fast = factories.BuildFactory(name='fast', product=cls.plan.product)

        cls.post_data = {
            'summary': cls.plan.name,
            'from_plan': cls.plan.pk,
            'build': cls.build_fast.pk,
            'notes': 'Create new test run',
            'POSTING_TO_CREATE': 'YES',
        }

        super().setUpTestData()

        cls.post_data['manager'] = cls.tester.email
        cls.post_data['default_tester'] = cls.tester.email

        case_status_confirmed = TestCaseStatus.get_confirmed()

        cls.case_1 = factories.TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=case_status_confirmed,
            plan=[cls.plan])
        cls.case_1.save()  # will generate history object

        cls.case_2 = factories.TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=case_status_confirmed,
            plan=[cls.plan])
        cls.case_2.save()  # will generate history object

        cls.post_data['case'] = [cls.case_1.pk, cls.case_2.pk]

    def verify_post_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.view_testrun')

        response = self.client.post(self.url, self.post_data)
        last_run = TestRun.objects.last()

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[last_run.pk]))

        self.assertEqual(self.plan.name, last_run.summary)
        self.assertEqual(self.plan, last_run.plan)
        self.assertEqual(self.plan.product_version, last_run.product_version)
        self.assertEqual(None, last_run.stop_date)
        self.assertEqual('Create new test run', last_run.notes)
        self.assertEqual(self.build_fast, last_run.build)
        self.assertEqual(self.tester, last_run.manager)
        self.assertEqual(self.tester, last_run.default_tester)
        for case, case_run in zip((self.case_1, self.case_2),
                                  last_run.case_run.order_by('case')):
            self.assertEqual(case, case_run.case)
            self.assertEqual(None, case_run.tested_by)
            self.assertEqual(self.tester, case_run.assignee)
            self.assertEqual(case.history.latest().history_id, case_run.case_text_version)
            self.assertEqual(last_run.build, case_run.build)
            self.assertEqual(None, case_run.close_date)


class MenuAddCommentItemTestCase(PermissionsTestCase):
    permission_label = 'django_comments.add_comment'
    http_method_names = ['get']

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory()

        cls.url = reverse('testruns-get', args=[cls.test_run.pk])
        super().setUpTestData()

        cls.add_comment_html = \
            '<a href="#" class="addBlue9 js-show-commentdialog">{0}</a>' \
            .format(_('Add'))

        user_should_have_perm(cls.tester, 'testruns.view_testrun')

    def assert_on_testrun_page(self, response):
        self.assertContains(response, self.test_run.summary)
        self.assertContains(response, self.test_run.plan)
        self.assertContains(response, self.test_run.build)

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertContains(response, self.add_comment_html, html=True)

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def verify_get_without_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertNotContains(response, self.add_comment_html, html=True)
