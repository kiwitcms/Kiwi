# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import json
from http import HTTPStatus
from datetime import timedelta

from django.utils import formats
from django.urls import reverse
from django.conf import settings

from tcms.testcases.models import Bug
from tcms.testcases.models import BugSystem
from tcms.testruns.models import EnvRunValueMap
from tcms.testruns.models import TestCaseRunStatus
from tcms.testruns.models import TestRun

from tcms.tests import BaseCaseRun
from tcms.tests import BasePlanCase
from tcms.tests import user_should_have_perm
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import EnvPropertyFactory
from tcms.tests.factories import EnvValueFactory
from tcms.tests.factories import BuildFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TagFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class TestGetRun(BaseCaseRun):
    """Test get view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetRun, cls).setUpTestData()

    def test_404_if_non_existing_pk(self):
        url = reverse('testruns-get', args=[99999999])
        response = self.client.get(url)
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_get_a_run(self):
        url = reverse('testruns-get', args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)

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
        self.assertRedirects(response, reverse('plans-all'))

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
        for i, case in enumerate((self.case_1, self.case_2, self.case_3), 1):
            self.assertContains(
                response,
                '<a href="/case/{0}/">{0}</a>'.format(case.pk),
                html=True)
            self.assertContains(
                response,
                '<a id="link_{0}" class="blind_title_link js-case-summary" '
                'data-param="{0}">{1}</a>'.format(i, case.summary),
                html=True)

    def test_create_a_new_run(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        clone_data = {
            'summary': self.plan.name,
            'from_plan': self.plan.pk,
            'product': self.product.pk,
            'product_version': self.version.pk,
            'build': self.build_fast.pk,
            'errata_id': '',
            'manager': self.tester.email,
            'default_tester': self.tester.email,
            'estimated_time': '0',
            'notes': 'Clone new run',
            'case': [self.case_1.pk, self.case_2.pk],
            'do': 'clone_run',
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
        self.assertEqual(timedelta(0), new_run.estimated_time)
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
            self.assertEqual(new_run.environment_id, case_run.environment_id)
            self.assertEqual(None, case_run.running_date)
            self.assertEqual(None, case_run.close_date)


class CloneRunBaseTest(BaseCaseRun):

    def assert_one_run_clone_page(self, response):
        """Verify clone page for cloning one test run"""

        self.assertContains(
            response,
            '<input id="id_summary" maxlength="255" name="summary" '
            'type="text" value="{}" required>'.format(self.test_run.summary),
            html=True)

        for_loop_counter = 1
        for case_run in (self.case_run_1, self.case_run_2):
            self.assertContains(
                response,
                '<a href="/case/{0}/">{0}</a>'.format(case_run.case.pk),
                html=True)
            self.assertContains(
                response,
                '<a id="link_{0}" class="blind_title_link" '
                'href="javascript:toggleTestCaseContents(\'{0}\')">{1}</a>'.format(
                    for_loop_counter, case_run.case.summary),
                html=True)
            for_loop_counter += 1


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
        url = reverse('testruns-clone-with-caseruns', args=[self.test_run.pk])

        response = self.client.post(url, {}, follow=True)

        self.assertContains(response, 'At least one TestCase is required')

    def test_open_clone_page_by_selecting_case_runs(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        url = reverse('testruns-clone-with-caseruns', args=[self.test_run.pk])

        response = self.client.post(url, {'case_run': [self.case_run_1.pk, self.case_run_2.pk]})

        self.assert_one_run_clone_page(response)

    def assert_clone_a_run(self, reserve_status=False, reserve_assignee=True):
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
            'estimated_time': '0',
            'notes': '',
            'case': [self.case_run_1.case.pk, self.case_run_2.case.pk],
            'case_run_id': [self.case_run_1.pk, self.case_run_2.pk],
        }

        # Set clone settings

        if reserve_status:
            clone_data['keep_status'] = 'on'
        if reserve_assignee:
            clone_data['keep_assignee'] = 'on'

        url = reverse('testruns-new')
        response = self.client.post(url, clone_data)

        cloned_run = TestRun.objects.get(summary=new_summary)

        self.assertRedirects(
            response,
            reverse('testruns-get', args=[cloned_run.pk]))

        self.assert_cloned_run(self.test_run, cloned_run,
                               reserve_status=reserve_status,
                               reserve_assignee=reserve_assignee)

    def assert_cloned_run(self, origin_run, cloned_run,
                          reserve_status=False, reserve_assignee=True):
        # Assert clone settings result
        for origin_case_run, cloned_case_run in zip((self.case_run_1, self.case_run_2),
                                                    cloned_run.case_run.order_by('pk')):
            if not reserve_status and not reserve_assignee:
                self.assertEqual(TestCaseRunStatus.objects.get(name='IDLE'),
                                 cloned_case_run.case_run_status)
                self.assertEqual(origin_case_run.assignee, cloned_case_run.assignee)
                continue

            if reserve_status and reserve_assignee:
                self.assertEqual(origin_case_run.case_run_status,
                                 cloned_case_run.case_run_status)
                self.assertEqual(origin_case_run.assignee,
                                 cloned_case_run.assignee)
                continue

            if reserve_status and not reserve_assignee:
                self.assertEqual(origin_case_run.case_run_status,
                                 cloned_case_run.case_run_status)

                if origin_case_run.case.default_tester is not None:
                    expected_assignee = origin_case_run.case.default_tester
                else:
                    expected_assignee = self.test_run.default_tester

                self.assertEqual(expected_assignee, cloned_case_run.assignee)

                continue

            if not reserve_status and reserve_assignee:
                self.assertEqual(TestCaseRunStatus.objects.get(name='IDLE'),
                                 cloned_case_run.case_run_status)
                self.assertEqual(origin_case_run.assignee, cloned_case_run.assignee)

    def test_clone_a_run_with_default_clone_settings(self):
        self.assert_clone_a_run()

    def test_clone_a_run_by_reserving_status(self):
        self.assert_clone_a_run(reserve_status=True, reserve_assignee=False)

    def test_clone_a_run_by_reserving_both_status_assignee(self):
        self.assert_clone_a_run(reserve_status=True, reserve_assignee=True)

    def test_clone_a_run_by_not_reserve_both_status_assignee(self):
        self.assert_clone_a_run(reserve_status=False, reserve_assignee=False)


class TestSearchRuns(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super(TestSearchRuns, cls).setUpTestData()

        cls.search_runs_url = reverse('testruns-all')

    def test_search_runs(self):
        search_criteria = {'summary': 'run'}

        response = self.client.get(self.search_runs_url, search_criteria)

        self.assertContains(
            response,
            '<input id="id_summary" name="summary" value="run" type="text">',
            html=True)

        # Assert table with this ID exists. Because searching runs actually
        # happens in an AJAX requested from DataTable, no need to verify
        # search runs at this moment.
        self.assertContains(response, 'id="testruns_table"')


class TestAJAXSearchRuns(BaseCaseRun):
    """Test ajax_search view

    View method ajax_search is called by DataTable in a AJAX GET request. This
    test aims to test the search, so DataTable related behavior do not belong
    to test purpose, ignore it.
    """

    @classmethod
    def setUpTestData(cls):
        super(TestAJAXSearchRuns, cls).setUpTestData()

        cls.search_url = reverse('testruns-ajax_search')

        # Add more test runs for testing different search criterias

        cls.run_tester = UserFactory(username='run_tester',
                                     email='runtester@example.com')

        cls.product_issuetracker = ProductFactory(name='issuetracker')
        cls.version_issuetracker_0_1 = VersionFactory(
            value='0.1', product=cls.product_issuetracker)
        cls.version_issuetracker_1_2 = VersionFactory(
            value='1.2', product=cls.product_issuetracker)

        cls.plan_issuetracker = TestPlanFactory(
            name='Test issue tracker releases',
            author=cls.tester,
            owner=cls.tester,
            product=cls.product_issuetracker,
            product_version=cls.version_issuetracker_0_1)

        # Probably need more cases as well in order to create case runs to
        # test statistcis in search result

        cls.build_issuetracker_fast = BuildFactory(
            product=cls.product_issuetracker)

        cls.run_hotfix = TestRunFactory(
            summary='Fast verify hotfix',
            product_version=cls.version_issuetracker_0_1,
            plan=cls.plan_issuetracker,
            build=cls.build_issuetracker_fast,
            manager=cls.tester,
            default_tester=cls.run_tester,
            tag=[TagFactory(name='fedora'),
                 TagFactory(name='rhel')])

        cls.run_release = TestRunFactory(
            summary='Smoke test before release',
            product_version=cls.version_issuetracker_1_2,
            plan=cls.plan_issuetracker,
            build=cls.build_issuetracker_fast,
            manager=cls.tester,
            default_tester=cls.run_tester)

        cls.run_daily = TestRunFactory(
            summary='Daily test during sprint',
            product_version=cls.version_issuetracker_0_1,
            plan=cls.plan_issuetracker,
            build=cls.build_issuetracker_fast,
            manager=cls.tester,
            default_tester=cls.run_tester,
            tag=[TagFactory(name='rhel')])

        # test data for Issue #78
        # https://github.com/kiwitcms/Kiwi/issues/78
        cls.run_bogus_summary = TestRunFactory(
            summary=r"""A summary with backslash(\), single quotes(') and double quotes(")""",
            manager=cls.tester,
            default_tester=UserFactory(username='bogus_tester', email='bogus@example.com'))

        cls.search_data = {
            'action': 'search',
            # Add criteria for searching runs in each test

            # DataTable properties: pagination and sorting
            'sEcho': 1,
            'iDisplayStart': 0,
            # Make enough length to display all searched runs in one page
            'iDisplayLength': TestRun.objects.count() + 1,
            'iSortCol_0': 1,
            'sSortDir_0': 'asc',
            'iSortingCols': 1,
            # In the view, first column is not sortable.
            'bSortable_0': 'false',
            'bSortable_1': 'true',
            'bSortable_2': 'true',
            'bSortable_3': 'true',
            'bSortable_4': 'true',
            'bSortable_5': 'true',
            'bSortable_6': 'true',
            'bSortable_7': 'true',
            'bSortable_8': 'true',
            'bSortable_9': 'true',
            'bSortable_10': 'true',
            'bSortable_11': 'true',
        }

    def assert_found_runs(self, expected_found_runs, search_result):
        expected_runs_count = len(expected_found_runs)
        self.assertEqual(expected_runs_count, search_result['iTotalRecords'])
        self.assertEqual(expected_runs_count, search_result['iTotalDisplayRecords'])
        self.assertEqual(expected_runs_count, len(search_result['aaData']))

        # used for assertIn b/c on Postgres the order in which items
        # are returned is not guaranteed at all
        links_id = [r[0] for r in search_result['aaData']]
        links_summary = [r[1] for r in search_result['aaData']]

        for run in expected_found_runs:
            self.assertIn(
                "<a href='{}'>{}</a>".format(
                    reverse('testruns-get', args=[run.pk]), run.pk),
                links_id)
            self.assertIn(
                "<a href='{}'>{}</a>".format(
                    reverse('testruns-get', args=[run.pk]), run.summary),
                links_summary)

    def test_search_all_runs(self):
        response = self.client.get(self.search_url)

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_empty_search_result(self):
        response = self.client.get(self.search_url, {'build': 9999})

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([], search_result)

    def test_search_by_summary(self):
        response = self.client.get(self.search_url, {'summary': 'run'})

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([self.test_run, self.test_run_1], search_result)

    def test_search_by_product(self):
        response = self.client.get(self.search_url,
                                   {'product': self.product_issuetracker.pk})

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_product_and_version(self):
        query_criteria = {
            'product': self.product_issuetracker.pk,
            'product_version': self.version_issuetracker_1_2.pk,
        }
        response = self.client.get(self.search_url, query_criteria)

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([self.run_release], search_result)

    def test_search_by_product_and_build(self):
        query_criteria = {
            'product': self.product_issuetracker.pk,
            'build': self.build_issuetracker_fast.pk,
        }
        response = self.client.get(self.search_url, query_criteria)

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_product_and_other_product_build(self):
        query_criteria = {
            'product': self.product_issuetracker.pk,
            'build': self.build.pk,
        }
        response = self.client.get(self.search_url, query_criteria)

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([], search_result)

    def test_search_by_plan_name(self):
        response = self.client.get(self.search_url, {'plan': 'Issue'})

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_empty_plan_name(self):
        response = self.client.get(self.search_url, {'plan': ''})

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_by_plan_id(self):
        response = self.client.get(self.search_url, {'plan': self.plan.pk})

        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([self.test_run, self.test_run_1], search_result)

    def test_search_by_manager_or_default_tester(self):
        response = self.client.get(self.search_url, {'people_type': 'people',
                                                     'people': self.run_tester})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

        response = self.client.get(self.search_url, {'people_type': 'people',
                                                     'people': self.tester})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_by_manager(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'manager',
                                    'people': self.tester.username})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_by_non_existing_manager(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'manager',
                                    'people': 'nonexisting-manager'})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([], search_result)

    def test_search_by_default_tester(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'default_tester',
                                    'people': self.run_tester.username})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_non_existing_default_tester(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'default_tester',
                                    'people': 'nonexisting-default-tester'})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([], search_result)

    def test_search_running_runs(self):
        response = self.client.get(self.search_url, {'status': 'running'})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_finished_runs(self):
        response = self.client.get(self.search_url, {'status': 'finished'})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([], search_result)

    def test_search_by_tag(self):
        response = self.client.get(self.search_url, {'tag__name__in': 'rhel'})
        search_result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assert_found_runs([self.run_hotfix, self.run_daily],
                               search_result)


class TestLoadRunsOfOnePlan(BaseCaseRun):
    """
    When the user goes to Test Plan -> Runs tab this view gets loaded.
    It also uses a JSON template like AJAX search and it is succeptible to
    bad characters in the Test Run summary.
    """

    @classmethod
    def setUpTestData(cls):
        super(TestLoadRunsOfOnePlan, cls).setUpTestData()

        # test data for Issue #78
        # https://github.com/kiwitcms/Kiwi/issues/78
        cls.run_bogus_summary = TestRunFactory(
            summary=r"""A summary with backslash(\), single quotes(') and double quotes(")""",
            plan=cls.plan)

        # test data for Issue #234
        # https://github.com/kiwitcms/Kiwi/issues/234
        cls.run_with_angle_brackets = TestRunFactory(
            summary=r"""A summary with <angle> brackets in <summary>""",
            plan=cls.plan)

    def test_load_runs(self):
        load_url = reverse('load_runs_of_one_plan_url', args=[self.plan.pk])
        response = self.client.get(load_url, {'plan': self.plan.pk})

        # verify JSON can be parsed correctly (for #78)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        # verify there is the same number of objects loaded
        self.assertEqual(TestRun.objects.filter(plan=self.plan).count(), data['iTotalRecords'])
        self.assertEqual(TestRun.objects.filter(plan=self.plan).count(),
                         data['iTotalDisplayRecords'])

    def test_with_angle_brackets(self):
        load_url = reverse('load_runs_of_one_plan_url', args=[self.plan.pk])
        response = self.client.get(load_url, {'plan': self.plan.pk})

        # verify JSON can be parsed correctly (for #234)
        # we can't really validate that the angle brackets are shown correctly
        # because the rendering is done by jQuery dataTables on the browser
        # and the default Django client does not support JavaScript!
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        # verify there is the same number of objects loaded
        self.assertEqual(TestRun.objects.filter(plan=self.plan).count(), data['iTotalRecords'])
        self.assertEqual(TestRun.objects.filter(plan=self.plan).count(),
                         data['iTotalDisplayRecords'])


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
        self.assertEqual(len(expected_cc), self.test_run.cc.count())

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


class TestEnvValue(BaseCaseRun):
    """Test env_value view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestEnvValue, cls).setUpTestData()

        cls.property_os = EnvPropertyFactory(name='os')
        cls.value_linux = EnvValueFactory(value='Linux',
                                          property=cls.property_os)
        cls.value_bsd = EnvValueFactory(value='BSD',
                                        property=cls.property_os)
        cls.value_mac = EnvValueFactory(value='Mac',
                                        property=cls.property_os)

        cls.test_run.add_env_value(cls.value_linux)
        cls.test_run_1.add_env_value(cls.value_linux)

        cls.env_value_url = reverse('testruns-env_value')
        user_should_have_perm(cls.tester, 'testruns.add_envrunvaluemap')
        user_should_have_perm(cls.tester, 'testruns.delete_envrunvaluemap')

    def test_refuse_if_action_is_unknown(self):
        response = self.client.get(self.env_value_url, {
            'env_value_id': self.value_bsd,
            'run_id': self.test_run.pk
        })

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Unrecognizable actions'})

    def test_add_env_value(self):
        self.client.get(self.env_value_url, {
            'a': 'add',
            'env_value_id': self.value_bsd.pk,
            'run_id': self.test_run.pk
        })

        rel = EnvRunValueMap.objects.filter(run=self.test_run, value=self.value_bsd)
        self.assertTrue(rel.exists())

    def test_add_env_value_to_runs(self):
        self.client.get(self.env_value_url, {
            'a': 'add',
            'env_value_id': self.value_bsd.pk,
            'run_id': [self.test_run.pk, self.test_run_1.pk]
        })

        rel = EnvRunValueMap.objects.filter(run=self.test_run,
                                            value=self.value_bsd)
        self.assertTrue(rel.exists())

        rel = EnvRunValueMap.objects.filter(run=self.test_run_1,
                                            value=self.value_bsd)
        self.assertTrue(rel.exists())

    def test_delete_env_value(self):
        self.client.get(self.env_value_url, {
            'a': 'remove',
            'env_value_id': self.value_linux.pk,
            'run_id': self.test_run.pk,
        })

        rel = EnvRunValueMap.objects.filter(run=self.test_run,
                                            value=self.value_linux)
        self.assertFalse(rel.exists())

    def test_delete_env_value_from_runs(self):
        self.client.get(self.env_value_url, {
            'a': 'remove',
            'env_value_id': self.value_linux.pk,
            'run_id': [self.test_run.pk, self.test_run_1.pk],
        })

        rel = EnvRunValueMap.objects.filter(run=self.test_run,
                                            value=self.value_linux)
        self.assertFalse(rel.exists())

        rel = EnvRunValueMap.objects.filter(run=self.test_run_1,
                                            value=self.value_linux)
        self.assertFalse(rel.exists())


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

    def test_remove_bug_from_case_run(self):
        post_data = {
            'a': 'remove',
            'case_run': self.case_run_1.pk,
            'bug_id': self.bug_12345,
        }

        response = self.client.get(self.case_run_bug_url, post_data)

        bug_exists = Bug.objects.filter(
            bug_id=self.bug_12345,
            case=self.case_run_1.case,
            case_run=self.case_run_1).exists()
        self.assertFalse(bug_exists)

        self.assertJsonResponse(
            response,
            {'rc': 0, 'response': 'ok', 'run_bug_count': 1})


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
        response = self.client.post(
            self.remove_case_run_url,
            {
                'case_run': [case_run.pk for case_run
                             in self.test_run.case_run.all()]
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

        cls.new_product = ProductFactory(name='Nitrate Dev')
        cls.new_build = BuildFactory(name='FastTest',
                                     product=cls.new_product)
        cls.new_version = VersionFactory(value='dev0.1',
                                         product=cls.new_product)
        cls.intern = UserFactory(username='intern',
                                 email='intern@example.com')

    def test_404_if_edit_non_existing_run(self):
        url = reverse('testruns-edit', args=[9999])
        response = self.client.get(url)

        self.assert404(response)

    def test_edit_run(self):

        post_data = {
            'summary': 'New run summary',
            'product': self.new_product.pk,
            'product_version': self.new_version.pk,
            'build': self.new_build.pk,
            'errata_id': '',
            'manager': self.test_run.manager.email,
            'default_tester': self.intern.email,
            'estimated_time': '00:03:00',
            'notes': 'easytest',
        }

        response = self.client.post(self.edit_url, post_data)

        run = TestRun.objects.get(pk=self.test_run.pk)
        self.assertEqual('New run summary', run.summary)
        self.assertEqual(self.new_version, run.product_version)
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
