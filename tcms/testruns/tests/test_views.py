# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

from http import HTTPStatus

from django.utils import formats
from django.urls import reverse
from django.contrib.auth.models import Permission

from tcms.testcases.models import BugSystem
from tcms.testruns.models import TestCaseRunStatus
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

        for _ in range(3):
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
                (self.case_run_1, self.case_run_2, self.case_run_3), 1):
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
        self.assertContains(response, 'Creating a TestRun requires at least one TestCase')

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
            self.assertEqual(TestCaseRunStatus.objects.get(name='IDLE'),
                             case_run.case_run_status)
            self.assertEqual(0, case_run.case_text_version)
            self.assertEqual(new_run.build, case_run.build)
            self.assertEqual(None, case_run.running_date)
            self.assertEqual(None, case_run.close_date)


class CloneRunBaseTest(BaseCaseRun):

    def assert_one_run_clone_page(self, response):
        """Verify clone page for cloning one test run"""

        self.assertContains(
            response,
            '<input id="id_summary" class="form-control" name="summary" '
            'type="text" value="Clone of {}" required>'.format(self.test_run.summary),
            html=True)

        for case_run in (self.case_run_1, self.case_run_2):
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

        self.assertContains(response, 'At least one TestCase is required')

    def test_open_clone_page_by_selecting_case_runs(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        url = reverse('testruns-clone', args=[self.test_run.pk])

        response = self.client.post(url, {'case_run': [self.case_run_1.pk, self.case_run_2.pk]})

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
            'case': [self.case_run_1.case.pk, self.case_run_2.case.pk],
            'case_run_id': [self.case_run_1.pk, self.case_run_2.pk],
        }

        url = reverse('testruns-new')
        response = self.client.post(url, clone_data)

        cloned_run = TestRun.objects.get(summary=new_summary)

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[cloned_run.pk]))

        self.assert_cloned_run(cloned_run)

    def assert_cloned_run(self, cloned_run):
        # Assert clone settings result
        for origin_case_run, cloned_case_run in zip((self.case_run_1, self.case_run_2),
                                                    cloned_run.case_run.order_by('pk')):
            self.assertEqual(TestCaseRunStatus.objects.get(name='IDLE'),
                             cloned_case_run.case_run_status)
            self.assertEqual(origin_case_run.assignee, cloned_case_run.assignee)


class TestSearchRuns(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super(TestSearchRuns, cls).setUpTestData()

        cls.search_runs_url = reverse('testruns-search')

    def test_search_page_is_shown(self):
        response = self.client.get(self.search_runs_url)
        self.assertContains(response, '<input id="id_summary" type="text"')


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
        response = self.client.get(self.cc_url,
                                   {'user': self.cc_user_1.username})
        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])

    def test_add_cc(self):
        response = self.client.get(
            self.cc_url,
            {'do': 'add', 'user': self.cc_user_1.username})

        self.assert_cc(response,
                       [self.cc_user_2, self.cc_user_3, self.cc_user_1])

    def test_remove_cc(self):
        response = self.client.get(
            self.cc_url,
            {'do': 'remove', 'user': self.cc_user_2.username})

        self.assert_cc(response, [self.cc_user_3])

    def test_refuse_to_remove_if_missing_user(self):
        response = self.client.get(self.cc_url, {'do': 'remove'})

        self.assertContains(
            response,
            'User name or email is required by this operation')

        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])

    def test_refuse_to_add_if_missing_user(self):
        response = self.client.get(self.cc_url, {'do': 'add'})

        self.assertContains(
            response,
            'User name or email is required by this operation')

        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])

    def test_refuse_if_user_not_exist(self):
        response = self.client.get(self.cc_url,
                                   {'do': 'add', 'user': 'not exist'})

        self.assertContains(
            response,
            'The user you typed does not exist in database')

        self.assert_cc(response, [self.cc_user_2, self.cc_user_3])


class TestBugActions(BaseCaseRun):
    """Test bug view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestBugActions, cls).setUpTestData()

        user_should_have_perm(cls.tester, 'testruns.change_testrun')
        user_should_have_perm(cls.tester, 'testcases.delete_bug')

        cls.bugzilla = BugSystem.objects.get(name='Bugzilla')
        cls.jira = BugSystem.objects.get(name='JIRA')

        cls.case_run_bug_url = reverse('testruns-bug', args=[cls.case_run_1.pk])

        cls.bug_12345 = '12345'
        cls.jira_kiwi_100 = 'KIWI-100'
        cls.case_run_1.add_bug(cls.bug_12345, bug_system_id=cls.bugzilla.pk)
        cls.case_run_1.add_bug(cls.jira_kiwi_100, bug_system_id=cls.jira.pk)

    def test_404_if_case_run_id_not_exist(self):
        self.case_run_bug_url = reverse('testruns-bug', args=[999])

        response = self.client.get(self.case_run_bug_url, {})
        self.assert404(response)

    def test_refuse_if_action_is_unknown(self):
        post_data = {
            'a': 'unknown action',
            'case_run': self.case_run_1.pk,
            'case': self.case_run_1.case.pk,
            'bug_system_id': BugSystem.objects.get(name='Bugzilla').pk,
            'bug_id': '123456',
        }

        response = self.client.get(self.case_run_bug_url, post_data)

        self.assertJsonResponse(
            response,
            {'rc': 1, 'response': 'Unrecognizable actions'})


class TestRemoveCaseRuns(BaseCaseRun):
    """Test remove_case_run view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestRemoveCaseRuns, cls).setUpTestData()

        user_should_have_perm(cls.tester, 'testruns.delete_testcaserun')

        cls.remove_case_run_url = reverse('testruns-remove_case_run',
                                          args=[cls.test_run.pk])

    def test_nothing_change_if_no_case_run_passed(self):
        response = self.client.post(self.remove_case_run_url, {})

        self.assertRedirects(response,
                             reverse('testruns-get', args=[self.test_run.pk]))

    def test_ignore_non_integer_case_run_ids(self):
        expected_rest_case_runs_count = self.test_run.case_run.count() - 2

        self.client.post(self.remove_case_run_url,
                         {
                             'case_run': [self.case_run_1.pk,
                                          'a1000',
                                          self.case_run_2.pk],
                         })

        self.assertEqual(expected_rest_case_runs_count,
                         self.test_run.case_run.count())

    def test_remove_case_runs(self):
        expected_rest_case_runs_count = self.test_run.case_run.count() - 1

        self.client.post(self.remove_case_run_url,
                         {'case_run': [self.case_run_1.pk]})

        self.assertEqual(expected_rest_case_runs_count,
                         self.test_run.case_run.count())

    def test_redirect_to_run_if_still_case_runs_exist_after_removal(self):
        response = self.client.post(self.remove_case_run_url,
                                    {'case_run': [self.case_run_1.pk]})

        self.assertRedirects(response,
                             reverse('testruns-get', args=[self.test_run.pk]))

    def test_redirect_to_add_case_runs_if_all_case_runs_are_removed(self):
        case_runs = []

        for case_run in self.test_run.case_run.all():
            case_runs.append(case_run.pk)

        response = self.client.post(
            self.remove_case_run_url,
            {
                'case_run': case_runs
            })

        self.assertRedirects(response,
                             reverse('add-cases-to-run',
                                     args=[self.test_run.pk]),
                             target_status_code=302)


class TestUpdateCaseRunText(BaseCaseRun):
    """Test update_case_run_text view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestUpdateCaseRunText, cls).setUpTestData()

        cls.update_url = reverse('testruns-update_case_run_text',
                                 args=[cls.test_run.pk])

        # To increase case text version
        cls.case_run_1.case.add_text(action='action',
                                     effect='effect',
                                     setup='setup',
                                     breakdown='breakdown')
        cls.case_run_1.case.add_text(action='action_1',
                                     effect='effect_1',
                                     setup='setup_1',
                                     breakdown='breakdown_1')

    def test_update_selected_case_runs(self):
        response = self.client.post(self.update_url,
                                    {'case_run': [self.case_run_1.pk]},
                                    follow=True)

        self.assertContains(response, '1 CaseRun(s) updated:')

        self.assertEqual(self.case_run_1.case.latest_text_version(),
                         self.case_run_1.latest_text().case_text_version)


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

        user_should_have_perm(cls.tester, 'testruns.add_testcaserun')

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
            for html in html_pieces:
                self.assertContains(response, html, html=True)
