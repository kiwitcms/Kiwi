# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

import unittest
from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.testruns.models import TestExecutionStatus, TestRun
from tcms.tests import (BaseCaseRun, BasePlanCase, remove_perm_from_user,
                        user_should_have_perm)
from tcms.tests.factories import TagFactory, UserFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestGetRun(BaseCaseRun):
    """Test get view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

        for _i in range(3):
            cls.test_run.add_tag(TagFactory())

        cls.unauthorized = UserFactory()
        cls.unauthorized.set_password('password')
        cls.unauthorized.save()

        cls.unauthorized.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(cls.unauthorized, 'testruns.add_testruntag')
        remove_perm_from_user(cls.unauthorized, 'testruns.delete_testruntag')

    def test_404_if_non_existing_pk(self):
        url = reverse('testruns-get', args=[99999999])
        response = self.client.get(url)
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def test_get_a_run(self):
        url = reverse('testruns-get', args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, 'Add Tag')
        self.assertContains(response, 'js-remove-tag')

        for i, case_run in enumerate(
                (self.execution_1, self.execution_2, self.execution_3), 1):
            self.assertContains(
                response,
                '<a href="#caserun_{0}">#{0}</a>'.format(case_run.pk),
                html=True)
            self.assertContains(
                response,
                '<a id="link_{0}" href="#caserun_{1}" title="Expand test case">'
                '{2}</a>'.format(i, case_run.pk, case_run.case.summary),
                html=True)

    def test_get_run_without_permissions_to_add_or_remove_tags(self):
        self.client.logout()

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.unauthorized.username,
            password='password')

        url = reverse('testruns-get', args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertNotContains(response, 'Add Tag')
        self.assertNotContains(response, 'js-remove-tag')


class TestCreateNewRun(BasePlanCase):
    """Test creating new run"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        user_should_have_perm(cls.tester, 'testruns.add_testrun')
        user_should_have_perm(cls.tester, 'testruns.view_testrun')
        cls.url = reverse('testruns-new')

    def test_refuse_if_missing_plan_pk(self):
        user_should_have_perm(self.tester, 'testplans.view_testplan')

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.post(self.url, {})
        self.assertRedirects(response, reverse('plans-search'))

    def test_refuse_if_missing_cases_pks(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.post(self.url, {'from_plan': self.plan.pk}, follow=True)
        self.assertContains(response, _('Creating a TestRun requires at least one TestCase'))

    def test_show_create_new_run_page(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(self.url, {
            'from_plan': self.plan.pk,
            'case': [self.case_1.pk, self.case_2.pk, self.case_3.pk]
        })

        # Assert listed cases
        for _i, case in enumerate((self.case_1, self.case_2, self.case_3), 1):
            case_url = reverse('testcases-get', args=[case.pk])
            self.assertContains(
                response,
                '<a href="%s">TC-%d: %s</a>' % (case_url, case.pk, case.summary),
                html=True)


class CloneRunBaseTest(BaseCaseRun):

    def assert_one_run_clone_page(self, response):
        """Verify clone page for cloning one test run"""

        self.assertContains(
            response,
            '<input id="id_summary" class="form-control" name="summary" '
            'type="text" value="%s%s" required>' % (_('Clone of '), self.test_run.summary),
            html=True)

        for case_run in (self.execution_1, self.execution_2):
            case_url = reverse('testcases-get', args=[case_run.case.pk])

            self.assertContains(
                response,
                '<a href="%s">TC-%d: %s</a>' % (case_url, case_run.case.pk, case_run.case.summary),
                html=True)


class TestStartCloneRunFromRunPage(CloneRunBaseTest):
    """Test case for cloning run from a run page"""

    @classmethod
    def setUpTestData(cls):
        super(TestStartCloneRunFromRunPage, cls).setUpTestData()

        cls.permission = 'testruns.add_testrun'
        user_should_have_perm(cls.tester, cls.permission)
        user_should_have_perm(cls.tester, 'testruns.view_testrun')

    def test_refuse_without_selecting_case_runs(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        url = reverse('testruns-clone', args=[self.test_run.pk])

        response = self.client.post(url, {}, follow=True)

        self.assertContains(response, _('At least one TestCase is required'))

    def test_open_clone_page_by_selecting_case_runs(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        url = reverse('testruns-clone', args=[self.test_run.pk])

        response = self.client.post(url, {'case_run': [self.execution_1.pk, self.execution_2.pk]})

        self.assert_one_run_clone_page(response)

    def test_clone_a_run(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        new_summary = 'Clone {} - {}'.format(self.test_run.pk, self.test_run.summary)

        clone_data = {
            'summary': new_summary,
            'from_plan': self.plan.pk,
            'product_id': self.test_run.plan.product_id,
            'do': 'clone_run',
            'POSTING_TO_CREATE': 'YES',
            'product': self.test_run.plan.product_id,
            'product_version': self.test_run.product_version.pk,
            'build': self.test_run.build.pk,
            'errata_id': '',
            'manager': self.test_run.manager.email,
            'default_tester': self.test_run.default_tester.email,
            'notes': '',
            'case': [self.execution_1.case.pk, self.execution_2.case.pk],
            'execution_id': [self.execution_1.pk, self.execution_2.pk],
        }

        url = reverse('testruns-new')
        response = self.client.post(url, clone_data)

        cloned_run = TestRun.objects.get(summary=new_summary)

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[cloned_run.pk]))

        self.assert_cloned_run(cloned_run)

    def test_clone_a_run_without_permissions(self):
        remove_perm_from_user(self.tester, 'testruns.add_testrun')
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        new_summary = 'Clone {} - {}'.format(self.test_run.pk, self.test_run.summary)

        clone_data = {
            'summary': new_summary,
            'from_plan': self.plan.pk,
            'product_id': self.test_run.plan.product_id,
            'do': 'clone_run',
            'POSTING_TO_CREATE': 'YES',
            'product': self.test_run.plan.product_id,
            'product_version': self.test_run.product_version.pk,
            'build': self.test_run.build.pk,
            'errata_id': '',
            'manager': self.test_run.manager.email,
            'default_tester': self.test_run.default_tester.email,
            'notes': '',
            'case': [self.execution_1.case.pk, self.execution_2.case.pk],
            'execution_id': [self.execution_1.pk, self.execution_2.pk],
        }

        url = reverse('testruns-new')
        response = self.client.post(url, clone_data)

        self.assertRedirects(
            response,
            reverse('tcms-login') + '?next=' + url)

    def assert_cloned_run(self, cloned_run):
        # Assert clone settings result
        for origin_case_run, cloned_case_run in zip((self.execution_1, self.execution_2),
                                                    cloned_run.case_run.order_by('pk')):
            self.assertEqual(TestExecutionStatus.objects.filter(weight=0).first(),
                             cloned_case_run.status)
            self.assertEqual(origin_case_run.assignee, cloned_case_run.assignee)


class TestSearchRuns(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super(TestSearchRuns, cls).setUpTestData()

        cls.search_runs_url = reverse('testruns-search')
        user_should_have_perm(cls.tester, 'testruns.view_testrun')

    def test_search_page_is_shown(self):
        response = self.client.get(self.search_runs_url)
        self.assertContains(response, '<input id="id_summary" type="text"')

    def test_search_page_is_shown_with_get_parameter_used(self):
        response = self.client.get(self.search_runs_url, {'product': self.product.pk})
        self.assertContains(response,
                            '<option value="%d" selected>%s</option>' % (self.product.pk,
                                                                         self.product.name),
                            html=True)


class TestRunCasesMenu(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, 'testruns.view_testrun')

        cls.url = reverse('testruns-get', args=[cls.test_run.pk])

        cls.add_cases_html = '<a href="{0}" class="addBlue9">{1}</a>'

        cls.remove_cases_html = \
            '<a href="#" title="{0}" data-param="{1}" \
            class="removeBlue9 js-del-case">{2}</a>' \
            .format(
                _('Remove selected cases form this test run'),
                cls.test_run.pk,
                _('Remove')
            )

        cls.update_case_run_text_html = \
            '<a href="#" title="{0}" \
            class="updateBlue9" id="update_case_run_text">{1}</a>' \
            .format(
                _('Update the IDLE case runs to newest case text'),
                _('Update')
            )

        cls.change_assignee_html = \
            '<a href="#" title="{0}" \
            class="assigneeBlue9 js-change-assignee">{1}</a>' \
            .format(
                _('Assign this case(s) to other people'),
                _('Assignee')
            )

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def test_add_cases_to_run_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.add_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.add_cases_html, html=True)

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def test_remove_cases_from_run_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.delete_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.remove_cases_html, html=True)

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def test_update_caserun_text_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.update_case_run_text_html, html=True)

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def test_change_assignee_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.change_assignee_html, html=True)

    def test_add_cases_to_run_without_permission(self):
        remove_perm_from_user(self.tester, 'testruns.add_testexecution')
        response = self.client.get(self.url)
        self.assertNotContains(response, self.add_cases_html, html=True)

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def test_remove_cases_from_run_without_permission(self):
        remove_perm_from_user(self.tester, 'testruns.delete_testexecution')
        response = self.client.get(self.url)
        self.assertNotContains(response, self.remove_cases_html, html=True)

    def test_update_caserun_text_without_permission(self):
        remove_perm_from_user(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertNotContains(response, self.update_case_run_text_html, html=True)

    def test_change_assignee_without_permission(self):
        remove_perm_from_user(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertNotContains(response, self.change_assignee_html, html=True)


class TestRunStatusMenu(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse('testruns-get', args=[cls.test_run.pk])
        user_should_have_perm(cls.tester, 'testruns.view_testrun')
        cls.status_menu_html = []

        for execution_status in TestExecutionStatus.objects.all():
            cls.status_menu_html.append(
                '<i class="{0}" style="color: {1}"></i>{2}'
                .format(execution_status.icon, execution_status.color, execution_status.name)
            )

    # TODO: un-skip this test, when the whole template has been refactored
    @unittest.skip('not implemented yet')
    def test_get_status_options_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertEqual(HTTPStatus.OK, response.status_code)

        for html_code in self.status_menu_html:
            self.assertContains(response, html_code, html=True)

    def test_get_status_options_without_permission(self):
        remove_perm_from_user(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertEqual(HTTPStatus.OK, response.status_code)

        for _tcrs in TestExecutionStatus.objects.all():
            self.assertNotContains(response, self.status_menu_html, html=True)


class TestChangeTestRunStatus(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse('testruns-change_status', args=[cls.test_run.pk])
        user_should_have_perm(cls.tester, 'testruns.view_testrun')

    def test_change_status_to_finished(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(self.url, {'finished': 1})
        self.assertRedirects(
            response,
            reverse('testruns-get', args=[self.test_run.pk]))

        self.test_run.refresh_from_db()
        self.assertIsNotNone(self.test_run.stop_date)

    def test_change_status_to_running(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(self.url, {'finished': 0})

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[self.test_run.pk]))

        self.test_run.refresh_from_db()
        self.assertIsNone(self.test_run.stop_date)

    def test_should_throw_404_on_non_existing_testrun(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(reverse('testruns-change_status', args=[99999]), {'finished': 0})
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_should_fail_when_try_to_change_status_without_permissions(self):
        remove_perm_from_user(self.tester, 'testruns.change_testrun')
        self.assertRedirects(
            self.client.get(self.url, {'finished': 1}),
            reverse('tcms-login') + '?next=%s?finished=1' % self.url)
