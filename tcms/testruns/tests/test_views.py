# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

import html
from http import HTTPStatus

from django.utils import formats
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import Permission
from django.utils.translation import ugettext_lazy as _

from tcms.testruns.models import TestExecutionStatus
from tcms.testruns.models import TestRun
from tcms.utils.permissions import initiate_user_with_default_setups

from tcms.tests import BaseCaseRun
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import BuildFactory
from tcms.tests.factories import TagFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import UserFactory


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
        super(TestCreateNewRun, cls).setUpTestData()

        cls.permission = 'testruns.add_testrun'
        user_should_have_perm(cls.tester, cls.permission)
        cls.url = reverse('testruns-new')
        cls.build_fast = BuildFactory(name='fast', product=cls.product)

    def test_refuse_if_missing_plan_pk(self):
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

    def test_create_a_new_run(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        clone_data = {
            'summary': self.plan.name,
            'from_plan': self.plan.pk,
            'build': self.build_fast.pk,
            'manager': self.tester.email,
            'default_tester': self.tester.email,
            'notes': 'Clone new run',
            'case': [self.case_1.pk, self.case_2.pk],
            'POSTING_TO_CREATE': 'YES',
        }

        url = reverse('testruns-new')
        response = self.client.post(url, clone_data)

        new_run = TestRun.objects.last()

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[new_run.pk]))

        self.assertEqual(self.plan.name, new_run.summary)
        self.assertEqual(self.plan, new_run.plan)
        self.assertEqual(self.version, new_run.product_version)
        self.assertEqual(None, new_run.stop_date)
        self.assertEqual('Clone new run', new_run.notes)
        self.assertEqual(self.build_fast, new_run.build)
        self.assertEqual(self.tester, new_run.manager)
        self.assertEqual(self.tester, new_run.default_tester)

        for case, case_run in zip((self.case_1, self.case_2),
                                  new_run.case_run.order_by('case')):
            self.assertEqual(case, case_run.case)
            self.assertEqual(None, case_run.tested_by)
            self.assertEqual(self.tester, case_run.assignee)
            self.assertEqual(TestExecutionStatus.objects.get(name='IDLE'),
                             case_run.status)
            self.assertEqual(case.history.latest().history_id, case_run.case_text_version)
            self.assertEqual(new_run.build, case_run.build)
            self.assertEqual(None, case_run.close_date)

    def test_create_a_new_run_without_permissions_should_fail(self):
        remove_perm_from_user(self.tester, 'testruns.add_testrun')
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        clone_data = {
            'summary': self.plan.name,
            'from_plan': self.plan.pk,
            'build': self.build_fast.pk,
            'manager': self.tester.email,
            'default_tester': self.tester.email,
            'notes': 'Clone new run',
            'case': [self.case_1.pk, self.case_2.pk],
            'POSTING_TO_CREATE': 'YES',
        }

        url = reverse('testruns-new')

        self.assertRedirects(
            self.client.post(url, clone_data),
            reverse('tcms-login') + '?next=' + url)


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
            'orig_run_id': self.test_run.pk,
            'POSTING_TO_CREATE': 'YES',
            'product': self.test_run.plan.product_id,
            'product_version': self.test_run.product_version.pk,
            'build': self.test_run.build.pk,
            'errata_id': '',
            'manager': self.test_run.manager.email,
            'default_tester': self.test_run.default_tester.email,
            'notes': '',
            'case': [self.execution_1.case.pk, self.execution_2.case.pk],
            'case_run_id': [self.execution_1.pk, self.execution_2.pk],
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
            'orig_run_id': self.test_run.pk,
            'POSTING_TO_CREATE': 'YES',
            'product': self.test_run.plan.product_id,
            'product_version': self.test_run.product_version.pk,
            'build': self.test_run.build.pk,
            'errata_id': '',
            'manager': self.test_run.manager.email,
            'default_tester': self.test_run.default_tester.email,
            'notes': '',
            'case': [self.execution_1.case.pk, self.execution_2.case.pk],
            'case_run_id': [self.execution_1.pk, self.execution_2.pk],
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
            self.assertEqual(TestExecutionStatus.objects.get(name='IDLE'),
                             cloned_case_run.status)
            self.assertEqual(origin_case_run.assignee, cloned_case_run.assignee)


class TestSearchRuns(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super(TestSearchRuns, cls).setUpTestData()

        cls.search_runs_url = reverse('testruns-search')

    def test_search_page_is_shown(self):
        response = self.client.get(self.search_runs_url)
        self.assertContains(response, '<input id="id_summary" type="text"')

    def test_search_page_is_shown_with_get_parameter_used(self):
        response = self.client.get(self.search_runs_url, {'product': self.product.pk})
        self.assertContains(response,
                            '<option value="%d" selected>%s</option>' % (self.product.pk,
                                                                         self.product.name),
                            html=True)


class TestAddRemoveRunCC(BaseCaseRun):
    """Test view tcms.testruns.views.cc"""

    @classmethod
    def setUpTestData(cls):
        super(TestAddRemoveRunCC, cls).setUpTestData()

        cls.cc_url = reverse('testruns-cc', args=[cls.test_run.pk])

        cls.cc_user_1 = UserFactory(username='cc-user-1',
                                    email='cc-user-1@example.com')
        cls.cc_user_2 = UserFactory(username='cc-user-2',
                                    email='cc-user-2@example.com')
        cls.cc_user_3 = UserFactory(username='cc-user-3',
                                    email='cc-user-3@example.com')

        cls.test_run.add_cc(cls.cc_user_2)
        cls.test_run.add_cc(cls.cc_user_3)

    def test_404_if_run_not_exist(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        cc_url = reverse('testruns-cc', args=[999999])
        response = self.client.get(cc_url)
        self.assert404(response)

    def assert_cc(self, response, expected_cc):
        self.assertEqual(len(expected_cc), self.test_run.cc.count())  # pylint: disable=no-member

        for cc in expected_cc:
            href = reverse('tcms-profile', args=[cc.username])
            self.assertContains(
                response,
                '<a href="%s">%s</a>' % (href, cc.username),
                html=True)

    def test_refuse_if_missing_action(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(self.cc_url,
                                   {'user': self.cc_user_1.username})
        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])

    def test_add_cc(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(
            self.cc_url,
            {'do': 'add', 'user': self.cc_user_1.username})

        self.assert_cc(response,
                       [self.cc_user_2, self.cc_user_3, self.cc_user_1])

    def test_remove_cc(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(
            self.cc_url,
            {'do': 'remove', 'user': self.cc_user_2.username})

        self.assert_cc(response, [self.cc_user_3])

    def test_refuse_to_remove_if_missing_user(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(self.cc_url, {'do': 'remove'})

        response_text = html.unescape(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertIn(str(_('The user you typed does not exist in database')),
                      response_text)

        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])

    def test_refuse_to_add_if_missing_user(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(self.cc_url, {'do': 'add'})

        response_text = html.unescape(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertIn(str(_('The user you typed does not exist in database')),
                      response_text)

        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])

    def test_refuse_if_user_not_exist(self):
        user_should_have_perm(self.tester, 'testruns.change_testrun')
        response = self.client.get(self.cc_url,
                                   {'do': 'add', 'user': 'not exist'})

        response_text = html.unescape(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertIn(str(_('The user you typed does not exist in database')),
                      response_text)

        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])

    def test_should_not_be_able_use_cc_when_user_has_no_pemissions(self):
        remove_perm_from_user(self.tester, 'testruns.change_testrun')

        self.assertRedirects(
            self.client.get(self.cc_url),
            reverse('tcms-login') + '?next=%s' % self.cc_url
        )


class TestUpdateCaseRunText(BaseCaseRun):
    """Test update_case_run_text view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.testruns_url = reverse('testruns-get', args=[cls.test_run.pk])
        cls.update_url = reverse('testruns-update_case_run_text',
                                 args=[cls.test_run.pk])

        # To increase case text version
        cls.execution_1.case.text = "Scenario Version 1"
        cls.execution_1.case.save()

        cls.execution_1.case.text = "Scenario Version 2"
        cls.execution_1.case.save()

    def test_get_update_caserun_text_with_permissions(self):
        user_should_have_perm(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.testruns_url)
        self.assertContains(response, 'id="update_case_run_text"')

    def test_update_selected_case_runs_with_permissions(self):
        user_should_have_perm(self.tester, 'testruns.change_testexecution')

        self.assertNotEqual(self.execution_1.case.history.latest().history_id,
                            self.execution_1.case_text_version)

        expected_text = "%s: %s -> %s" % (
            self.execution_1.case.summary,
            self.execution_1.case_text_version,
            self.execution_1.case.history.latest().history_id
        )

        response = self.client.post(self.update_url,
                                    {'case_run': [self.execution_1.pk]},
                                    follow=True)

        self.assertContains(response, expected_text)

        self.execution_1.refresh_from_db()

        self.assertEqual(
            self.execution_1.case.get_text_with_version(
                self.execution_1.case_text_version
            ),
            "Scenario Version 2"
        )
        self.assertEqual(
            self.execution_1.case.history.latest().history_id,
            self.execution_1.case_text_version
        )

    def test_get_update_caserun_text_without_permissions(self):
        remove_perm_from_user(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.testruns_url)
        self.assertNotContains(response, 'id="update_case_run_text"')

    def test_update_selected_case_runs_without_permissions(self):
        self.execution_1.case.text = "Scenario Version 3"
        self.execution_1.case.save()

        remove_perm_from_user(self.tester, 'testruns.change_testexecution')

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        self.assertNotEqual(
            self.execution_1.case.history.latest().history_id,
            self.execution_1.case_text_version
        )

        response = self.client.post(self.update_url,
                                    {'case_run': [self.execution_1.pk]},
                                    follow=True)

        self.assertRedirects(
            response,
            reverse('tcms-login') + '?next=' + self.update_url
        )

        self.execution_1.refresh_from_db()

        self.assertNotEqual(
            self.execution_1.case.get_text_with_version(
                self.execution_1.case_text_version
            ),
            "Scenario Version 3"
        )

        self.assertNotEqual(
            self.execution_1.case.history.latest().history_id,
            self.execution_1.case_text_version
        )


class TestEditRun(BaseCaseRun):
    """Test edit view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestEditRun, cls).setUpTestData()

        user_should_have_perm(cls.tester, 'testruns.change_testrun')
        cls.edit_url = reverse('testruns-edit', args=[cls.test_run.pk])

        cls.new_build = BuildFactory(name='FastTest',
                                     product=cls.test_run.plan.product)
        cls.intern = UserFactory(username='intern',
                                 email='intern@example.com')

    def test_404_if_edit_non_existing_run(self):
        url = reverse('testruns-edit', args=[9999])
        response = self.client.get(url)

        self.assert404(response)

    def test_edit_run(self):

        post_data = {
            'summary': 'New run summary',
            'build': self.new_build.pk,
            'manager': self.test_run.manager.email,
            'default_tester': self.intern.email,
            'notes': 'easytest',
        }

        response = self.client.post(self.edit_url, post_data)

        run = TestRun.objects.get(pk=self.test_run.pk)
        self.assertEqual('New run summary', run.summary)
        self.assertEqual(self.new_build, run.build)

        self.assertRedirects(response, reverse('testruns-get', args=[run.pk]))


class TestAddCasesToRun(BaseCaseRun):
    """Test AddCasesToRunView"""

    @classmethod
    def setUpTestData(cls):
        super(TestAddCasesToRun, cls).setUpTestData()

        cls.proposed_case = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_proposed,
            plan=[cls.plan])

        user_should_have_perm(cls.tester, 'testruns.add_testexecution')

    def test_show_add_cases_to_run(self):
        url = reverse('add-cases-to-run', args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertNotContains(
            response,
            '<a href="{0}">{1}</a>'.format(
                reverse('testcases-get',
                        args=[self.proposed_case.pk]),
                self.proposed_case.pk),
            html=True
        )

        confirmed_cases = [self.case, self.case_1, self.case_2, self.case_3]

        # Check selected and unselected case id checkboxes
        # cls.case is not added to cls.test_run, so it should not be checked.
        self.assertContains(
            response,
            '<td align="left">'
            '<input type="checkbox" name="case" value="{0}">'
            '</td>'.format(self.case.pk),
            html=True)

        # other cases are added to cls.test_run, so must be checked.
        for case in confirmed_cases[1:]:
            self.assertContains(
                response,
                '<td align="left">'
                '<input type="checkbox" name="case" value="{0}" '
                'disabled="true" checked="true">'
                '</td>'.format(case.pk),
                html=True)

        # Check listed case properties
        # note: the response is ordered by 'case'
        for loop_counter, case in enumerate(confirmed_cases, 1):
            html_pieces = [
                '<a href="{0}">{1}</a>'.format(
                    reverse('testcases-get', args=[case.pk]),
                    case.pk),

                '<td class="js-case-summary" data-param="{0}">'
                '<a id="link_{0}" class="blind_title_link" '
                'href="javascript:void(0);">{1}</a></td>'.format(loop_counter,
                                                                 case.summary),

                '<td>{0}</td>'.format(case.author.username),
                '<td>{0}</td>'.format(
                    formats.date_format(case.create_date, 'DATETIME_FORMAT')),
                '<td>{0}</td>'.format(case.category.name),
                '<td>{0}</td>'.format(case.priority.value),
            ]
            for piece in html_pieces:
                self.assertContains(response, piece, html=True)


class TestRunCasesMenu(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.url = reverse('testruns-get', args=[cls.test_run.pk])

        cls.add_cases_html = \
            '<a href="{0}" class="addBlue9">{1}</a>' \
            .format(
                reverse('add-cases-to-run', args=[cls.test_run.pk]),
                _('Add')
            )

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
            href="javascript:void(0)" data-param="{1}" \
            class="updateBlue9 js-update-case" id="update_case_run_text">{2}</a>' \
            .format(
                _('Update the IDLE case runs to newest case text'),
                reverse('testruns-update_case_run_text', args=[cls.test_run.pk]),
                _('Update')
            )

        cls.change_assignee_html = \
            '<a href="#" title="{0}" \
            class="assigneeBlue9 js-change-assignee">{1}</a>' \
            .format(
                _('Assign this case(s) to other people'),
                _('Assignee')
            )

    def test_add_cases_to_run_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.add_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.add_cases_html, html=True)

    def test_remove_cases_from_run_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.delete_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.remove_cases_html, html=True)

    def test_update_caserun_text_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.update_case_run_text_html, html=True)

    def test_change_assignee_with_permission(self):
        user_should_have_perm(self.tester, 'testruns.change_testexecution')
        response = self.client.get(self.url)
        self.assertContains(response, self.change_assignee_html, html=True)

    def test_add_cases_to_run_without_permission(self):
        remove_perm_from_user(self.tester, 'testruns.add_testexecution')
        response = self.client.get(self.url)
        self.assertNotContains(response, self.add_cases_html, html=True)

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
        cls.status_menu_html = []

        for tcrs in TestExecutionStatus.objects.all():
            cls.status_menu_html.append(
                '<a value="{0}" href="#" class="{1}Blue9">{2}</a>'
                .format(tcrs.pk, tcrs.name.lower(), tcrs.name)
            )

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

        for tcrs in TestExecutionStatus.objects.all():
            self.assertNotContains(response, self.status_menu_html, html=True)


class TestExecutionComments(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse('testruns-get', args=[cls.test_run.pk])

        cls.add_comment_html = \
            '<a href="#" class="addBlue9 js-show-commentdialog">{0}</a>' \
            .format(_('Add'))

    def test_get_add_comment_with_permission(self):
        user_should_have_perm(self.tester, 'django_comments.add_comment')
        response = self.client.get(self.url)
        self.assertContains(response, self.add_comment_html, html=True)

    def test_get_add_comment_without_permission(self):
        remove_perm_from_user(self.tester, 'django_comments.add_comment')
        response = self.client.get(self.url)
        self.assertNotContains(response, self.add_comment_html, html=True)


class TestChangeTestRunStatus(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse('testruns-change_status', args=[cls.test_run.pk])

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
