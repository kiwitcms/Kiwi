# -*- coding: utf-8 -*-

import os
import json
from datetime import timedelta
from mock import patch
from six.moves import http_client
from xml.etree import ElementTree

from django.utils import formats
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from tcms.testcases.models import TestCaseBug
from tcms.testcases.models import TestCaseBugSystem
from tcms.testruns.models import TCMSEnvRunValueMap
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.testruns.models import TestRun

from tcms.tests import BaseCaseRun
from tcms.tests import BasePlanCase
from tcms.tests import user_should_have_perm
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import TCMSEnvPropertyFactory
from tcms.tests.factories import TCMSEnvValueFactory
from tcms.tests.factories import TestBuildFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestTagFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory


class TestOrderCases(BaseCaseRun):
    """Test view method order_case"""

    @classmethod
    def setUpTestData(cls):
        super(TestOrderCases, cls).setUpTestData()

    def test_404_if_run_does_not_exist(self):
        nonexisting_run_pk = TestRun.objects.last().pk + 1
        url = reverse('testruns-order_case', args=[nonexisting_run_pk])
        response = self.client.post(url)
        self.assert404(response)

    def test_prompt_if_no_case_run_is_passed(self):
        url = reverse('testruns-order_case', args=[self.test_run.pk])
        response = self.client.post(url)
        self.assertIn(
            'At least one case is required by re-oder in run',
            response.content)

    def test_order_case_runs(self):
        url = reverse('testruns-order_case', args=[self.test_run.pk])
        response = self.client.post(url, {'case_run': [self.case_run_1.pk,
                                                       self.case_run_2.pk,
                                                       self.case_run_3.pk]})

        redirect_to = reverse('testruns-get', args=[self.test_run.pk])
        self.assertRedirects(response, redirect_to)

        test_sortkeys = [
            TestCaseRun.objects.get(pk=self.case_run_1.pk).sortkey,
            TestCaseRun.objects.get(pk=self.case_run_2.pk).sortkey,
            TestCaseRun.objects.get(pk=self.case_run_3.pk).sortkey,
        ]
        self.assertEqual([10, 20, 30], test_sortkeys)


class TestGetRun(BaseCaseRun):
    """Test get view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetRun, cls).setUpTestData()

    def test_404_if_non_existing_pk(self):
        url = reverse('testruns-get', args=[99999999])
        response = self.client.get(url)
        self.assertEqual(http_client.NOT_FOUND, response.status_code)

    def test_get_a_run(self):
        url = reverse('testruns-get', args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(http_client.OK, response.status_code)

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
        cls.build_fast = TestBuildFactory(name='fast', product=cls.product)

    def test_refuse_if_missing_plan_pk(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.post(self.url, {})
        self.assertRedirects(response, reverse('plans-all'))

    def test_refuse_if_missing_cases_pks(self):
        self.client.login(username=self.tester.username, password='password')
        response = self.client.post(self.url, {'from_plan': self.plan.pk})
        self.assertContains(
            response,
            'At least one case is required by a run.')

    def test_show_create_new_run_page(self):
        self.client.login(username=self.tester.username, password='password')

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
        self.client.login(username=self.tester.username, password='password')

        clone_data = {
            'summary': self.plan.name,
            'from_plan': self.plan.pk,
            'product': self.product.pk,
            'product_version': self.version.pk,
            'build': self.build_fast.pk,
            'errata_id': '',
            'manager': self.tester.email,
            'default_tester': self.tester.email,
            'estimated_time': '0m',
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
        self.assertEqual(0, new_run.plan_text_version)
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
        self.client.login(username=self.tester.username, password='password')
        url = reverse('testruns-clone-with-caseruns', args=[self.test_run.pk])

        response = self.client.post(url, {})

        self.assertContains(
            response,
            'At least one case is required by a run')

    def test_open_clone_page_by_selecting_case_runs(self):
        self.client.login(username=self.tester.username, password='password')
        url = reverse('testruns-clone-with-caseruns', args=[self.test_run.pk])

        response = self.client.post(url, {'case_run': [self.case_run_1.pk, self.case_run_2.pk]})

        self.assert_one_run_clone_page(response)

    def assert_clone_a_run(self, reserve_status=False, reserve_assignee=True):
        self.client.login(username=self.tester.username, password='password')

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
            'estimated_time': '0m',
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


class TestStartCloneRunFromRunsSearchPage(CloneRunBaseTest):
    """Test case for cloning runs from runs search result page"""

    @classmethod
    def setUpTestData(cls):
        super(TestStartCloneRunFromRunsSearchPage, cls).setUpTestData()
        cls.clone_url = reverse('testruns-clone')
        cls.permission = 'testruns.add_testrun'

        cls.origin_run = TestRunFactory(product_version=cls.version,
                                        plan=cls.plan,
                                        build=cls.build,
                                        manager=cls.tester,
                                        default_tester=cls.tester)

        for tag_name in ('python', 'kiwi', 'django'):
            cls.origin_run.add_tag(TestTagFactory(name=tag_name))

        for cc in (User.objects.create_user(username='run_tester1',
                                            email='run_tester1@example.com'),
                   User.objects.create_user(username='run_tester2',
                                            email='run_tester2@example.com'),
                   User.objects.create_user(username='run_tester3',
                                            email='run_tester3@example.com'),
                   ):
            cls.origin_run.add_cc(cc)

        cls.property = TCMSEnvPropertyFactory(name='lang')
        for value in ('python', 'perl', 'ruby'):
            cls.origin_run.add_env_value(
                TCMSEnvValueFactory(value=value, property=cls.property))

        cls.case_2.add_text(action='action', effect='effect',
                            setup='setup', breakdown='breakdown')
        cls.case_2.add_text(action='action2', effect='effect2',
                            setup='setup2', breakdown='breakdown2')

        for case in (cls.case_1, cls.case_2):
            TestCaseRunFactory(assignee=cls.tester, tested_by=cls.tester,
                               build=cls.build, sortkey=10,
                               case_run_status=cls.case_run_status_idle,
                               run=cls.origin_run, case=case)

    def test_refuse_clone_without_selecting_runs(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.clone_url, {})

        self.assertContains(
            response,
            'At least one run is required')

    def test_open_clone_page_by_selecting_only_one_run(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.clone_url, {'run': self.test_run.pk})

        self.assert_one_run_clone_page(response)

    def test_open_clone_page_by_selecting_multiple_runs(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.get(self.clone_url,
                                   {'run': [self.test_run.pk, self.test_run_1.pk]})

        runs_li = [
            '''
            <li>
                <label for="id_run_0">
                    <input checked="checked" id="id_run_0" name="run" value="{0}" type="checkbox">
                    {1}
                </label>
            </li>
            '''.format(self.test_run.pk, self.test_run.summary),
            '''
            <li>
                <label for="id_run_1">
                    <input checked="checked" id="id_run_1" name="run" value="{0}" type="checkbox">
                    {1}
                </label>
            </li>
            '''.format(self.test_run_1.pk, self.test_run_1.summary),
        ]
        runs_ul = '<ul id="id_run">{}</ul>'.format(''.join(runs_li))

        self.assertContains(response, runs_ul, html=True)

        # Assert clone settings
        clone_settings_controls = [
            '<li><input checked="checked" id="id_update_case_text" name="update_case_text" '
            'type="checkbox">Use newest case text(setup/actions/effects/breakdown)</li>',
            '<li><input checked="checked" id="id_clone_cc" name="clone_cc" type="checkbox">'
            'Clone cc</li>',
            '<li><input checked="checked" id="id_clone_tag" name="clone_tag" type="checkbox">'
            'Clone tag</li>',
        ]
        for html_control in clone_settings_controls:
            self.assertContains(response, html_control, html=True)

    def test_clone_one_selected_run_with_default_clone_settings(self):
        self.assert_clone_runs([self.origin_run])

    def test_clone_one_selected_run_without_cloning_cc(self):
        self.assert_clone_runs([self.origin_run], clone_cc=False)

    def test_clone_one_selected_run_without_cloning_tag(self):
        self.assert_clone_runs([self.origin_run], clone_tag=False)

    def test_clone_one_selected_run_not_use_newest_case_text(self):
        self.assert_clone_runs([self.origin_run], update_case_text=False)

    def test_clone_all_selected_runs_with_default_clone_settings(self):
        self.assert_clone_runs([self.test_run, self.origin_run])

    def test_clone_all_selected_runs_without_cloning_cc(self):
        self.assert_clone_runs([self.test_run, self.origin_run], clone_cc=False)

    def test_clone_all_selected_runs_without_cloning_tag(self):
        self.assert_clone_runs([self.test_run, self.origin_run], clone_tag=False)

    def test_clone_one_selected_runs_not_use_newest_case_text(self):
        self.assert_clone_runs([self.test_run, self.origin_run], update_case_text=False)

    def assert_clone_runs(self, runs_to_clone,
                          clone_cc=True, clone_tag=True, update_case_text=True):
        """Test only clone the selected one run from runs/clone/"""
        self.client.login(username=self.tester.username, password='password')

        post_data = {
            'run': [run.pk for run in runs_to_clone],
            'product': self.origin_run.plan.product.pk,
            'product_version': self.origin_run.product_version.pk,
            'build': self.origin_run.build.pk,
            'manager': self.tester.username,
            'default_tester': self.tester.username,
            'submit': 'Clone',

            # Clone settings
            # Do not update manager
            'update_default_tester': 'on',
        }

        if clone_cc:
            post_data['clone_cc'] = 'on'
        if clone_tag:
            post_data['clone_tag'] = 'on'
        if update_case_text:
            post_data['update_case_text'] = 'on'

        response = self.client.post(self.clone_url, post_data)

        # grabs the last X runs, which should be the cloned ones
        # using reversed ordering b/c negative indexes are not supported
        cloned_runs = TestRun.objects.order_by('-pk').only('pk')[:len(runs_to_clone)]
        # then order by summary
        cloned_runs = TestRun.objects.filter(pk__in=[r.pk for r in cloned_runs]).order_by('summary')

        # convert to ordered query set so we can compare to it later using the same
        # ordering by summary as above
        runs_to_clone = TestRun.objects.filter(pk__in=post_data['run']).order_by('summary')

        if cloned_runs.count() == 1:
            # Finally, redirect to the new cloned test run
            self.assertRedirects(
                response,
                reverse('testruns-get', args=[cloned_runs[0].pk]))
        else:
            self.assertEqual(http_client.FOUND, response.status_code)

        for origin_run, cloned_run in zip(runs_to_clone, cloned_runs):
            self.assert_cloned_run(origin_run, cloned_run,
                                   clone_cc=clone_cc, clone_tag=clone_tag,
                                   use_newest_case_text=update_case_text)

    def assert_cloned_run(self, origin_run, cloned_run,
                          clone_cc=True, clone_tag=True, use_newest_case_text=True):
        self.assertEqual(origin_run.product_version, cloned_run.product_version)
        self.assertEqual(origin_run.plan_text_version, cloned_run.plan_text_version)
        self.assertEqual(origin_run.summary, cloned_run.summary)
        self.assertEqual(origin_run.notes, cloned_run.notes)
        self.assertEqual(origin_run.estimated_time, cloned_run.estimated_time)
        self.assertEqual(origin_run.plan, cloned_run.plan)
        self.assertEqual(origin_run.build, cloned_run.build)
        self.assertEqual(origin_run.manager, cloned_run.manager)
        self.assertEqual(self.tester, cloned_run.default_tester)

        for origin_case_run, cloned_case_run in zip(origin_run.case_run.order_by('case'),
                                                    cloned_run.case_run.order_by('case')):
            self.assertEqual(origin_case_run.case, cloned_case_run.case)
            self.assertEqual(origin_case_run.assignee, cloned_case_run.assignee)
            self.assertEqual(origin_case_run.build, cloned_case_run.build)
            self.assertEqual(origin_case_run.notes, cloned_case_run.notes)
            self.assertEqual(origin_case_run.sortkey, cloned_case_run.sortkey)

            if use_newest_case_text:
                if origin_case_run.case.text.count() == 0:
                    self.assertEqual(origin_case_run.case_text_version,
                                     cloned_case_run.case_text_version)
                else:
                    # Should use newest case text
                    self.assertEqual(list(origin_case_run.get_text_versions())[-1],
                                     cloned_case_run.case_text_version)
            else:
                self.assertEqual(origin_case_run.case_text_version,
                                 cloned_case_run.case_text_version)

        if clone_cc:
            self.assertEqual(list(origin_run.cc_list.values_list('user')),
                             list(cloned_run.cc_list.values_list('user')))
        else:
            self.assertEqual([], list(cloned_run.cc_list.all()))

        if clone_tag:
            self.assertEqual(list(origin_run.tags.values_list('tag')),
                             list(cloned_run.tags.values_list('tag')))
        else:
            self.assertEqual([], list(cloned_run.tags.all()))


class TestSearchRuns(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super(TestSearchRuns, cls).setUpTestData()

        cls.search_runs_url = reverse('testruns-all')

    def test_only_show_search_form(self):
        response = self.client.get(self.search_runs_url)
        self.assertContains(response, '<form id="runs_form"></form>', html=True)

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

        cls.build_issuetracker_fast = TestBuildFactory(
            product=cls.product_issuetracker)

        cls.run_hotfix = TestRunFactory(
            summary='Fast verify hotfix',
            product_version=cls.version_issuetracker_0_1,
            plan=cls.plan_issuetracker,
            build=cls.build_issuetracker_fast,
            manager=cls.tester,
            default_tester=cls.run_tester,
            tag=[TestTagFactory(name='fedora'),
                 TestTagFactory(name='rhel')])

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
            tag=[TestTagFactory(name='rhel')])

    def assert_found_runs(self, expected_found_runs, search_result):
        expected_runs_count = len(expected_found_runs)
        self.assertEqual(expected_runs_count, search_result['iTotalRecords'])
        self.assertEqual(expected_runs_count, search_result['iTotalDisplayRecords'])
        self.assertEqual(expected_runs_count, len(search_result['aaData']))

        # used for assertIn b/c on Postgres the order in which items
        # are returned is not guaranteed at all
        links_id = [r[1] for r in search_result['aaData']]
        links_summary = [r[2] for r in search_result['aaData']]

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

        search_result = json.loads(response.content)
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_empty_search_result(self):
        response = self.client.get(self.search_url, {'build': 9999})

        search_result = json.loads(response.content)
        self.assert_found_runs([], search_result)

    def test_search_by_summary(self):
        response = self.client.get(self.search_url, {'summary': 'run'})

        search_result = json.loads(response.content)
        self.assert_found_runs([self.test_run, self.test_run_1], search_result)

    def test_search_by_product(self):
        response = self.client.get(self.search_url,
                                   {'product': self.product_issuetracker.pk})

        search_result = json.loads(response.content)
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_product_and_version(self):
        query_criteria = {
            'product': self.product_issuetracker.pk,
            'product_version': self.version_issuetracker_1_2.pk,
        }
        response = self.client.get(self.search_url, query_criteria)

        search_result = json.loads(response.content)
        self.assert_found_runs([self.run_release], search_result)

    def test_search_by_product_and_build(self):
        query_criteria = {
            'product': self.product_issuetracker.pk,
            'build': self.build_issuetracker_fast.pk,
        }
        response = self.client.get(self.search_url, query_criteria)

        search_result = json.loads(response.content)
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_product_and_other_product_build(self):
        query_criteria = {
            'product': self.product_issuetracker.pk,
            'build': self.build.pk,
        }
        response = self.client.get(self.search_url, query_criteria)

        search_result = json.loads(response.content)
        self.assert_found_runs([], search_result)

    def test_search_by_plan_name(self):
        response = self.client.get(self.search_url, {'plan': 'Issue'})

        search_result = json.loads(response.content)
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_empty_plan_name(self):
        response = self.client.get(self.search_url, {'plan': ''})

        search_result = json.loads(response.content)
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_by_plan_id(self):
        response = self.client.get(self.search_url, {'plan': self.plan.pk})

        search_result = json.loads(response.content)
        self.assert_found_runs([self.test_run, self.test_run_1], search_result)

    def test_search_by_manager_or_default_tester(self):
        response = self.client.get(self.search_url, {'people_type': 'people',
                                                     'people': self.run_tester})
        search_result = json.loads(response.content)
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

        response = self.client.get(self.search_url, {'people_type': 'people',
                                                     'people': self.tester})
        search_result = json.loads(response.content)
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_by_manager(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'manager',
                                    'people': self.tester.username})
        search_result = json.loads(response.content)
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_by_non_existing_manager(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'manager',
                                    'people': 'nonexisting-manager'})
        search_result = json.loads(response.content)
        self.assert_found_runs([], search_result)

    def test_search_by_default_tester(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'default_tester',
                                    'people': self.run_tester.username})
        search_result = json.loads(response.content)
        self.assert_found_runs(
            [self.run_hotfix, self.run_release, self.run_daily],
            search_result)

    def test_search_by_non_existing_default_tester(self):
        response = self.client.get(self.search_url,
                                   {'people_type': 'default_tester',
                                    'people': 'nonexisting-default-tester'})
        search_result = json.loads(response.content)
        self.assert_found_runs([], search_result)

    def test_search_running_runs(self):
        response = self.client.get(self.search_url, {'status': 'running'})
        search_result = json.loads(response.content)
        self.assert_found_runs(TestRun.objects.all(), search_result)

    def test_search_finished_runs(self):
        response = self.client.get(self.search_url, {'status': 'finished'})
        search_result = json.loads(response.content)
        self.assert_found_runs([], search_result)

    def test_search_by_tag(self):
        response = self.client.get(self.search_url, {'tag__name__in': 'rhel'})
        search_result = json.loads(response.content)
        self.assert_found_runs([self.run_hotfix, self.run_daily],
                               search_result)


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
            self.assertContains(
                response,
                '<a href="mailto:{0}">{0}</a>'.format(cc.email),
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

        cls.property_os = TCMSEnvPropertyFactory(name='os')
        cls.value_linux = TCMSEnvValueFactory(value='Linux',
                                              property=cls.property_os)
        cls.value_bsd = TCMSEnvValueFactory(value='BSD',
                                            property=cls.property_os)
        cls.value_mac = TCMSEnvValueFactory(value='Mac',
                                            property=cls.property_os)

        cls.test_run.add_env_value(cls.value_linux)
        cls.test_run_1.add_env_value(cls.value_linux)

        cls.env_value_url = reverse('testruns-env_value')
        user_should_have_perm(cls.tester, 'testruns.add_tcmsenvrunvaluemap')
        user_should_have_perm(cls.tester, 'testruns.delete_tcmsenvrunvaluemap')

    def test_refuse_if_action_is_unknown(self):
        self.login_tester()

        response = self.client.get(self.env_value_url, {
            'env_value_id': self.value_bsd,
            'run_id': self.test_run.pk
        })

        self.assertEqual({'rc': 1, 'response': 'Unrecognizable actions'},
                         json.loads(response.content))

    def test_add_env_value(self):
        self.login_tester()

        self.client.get(self.env_value_url, {
            'a': 'add',
            'env_value_id': self.value_bsd.pk,
            'run_id': self.test_run.pk
        })

        rel = TCMSEnvRunValueMap.objects.filter(run=self.test_run,
                                                value=self.value_bsd)
        self.assertTrue(rel.exists())

    def test_add_env_value_to_runs(self):
        self.login_tester()

        self.client.get(self.env_value_url, {
            'a': 'add',
            'env_value_id': self.value_bsd.pk,
            'run_id': [self.test_run.pk, self.test_run_1.pk]
        })

        rel = TCMSEnvRunValueMap.objects.filter(run=self.test_run,
                                                value=self.value_bsd)
        self.assertTrue(rel.exists())

        rel = TCMSEnvRunValueMap.objects.filter(run=self.test_run_1,
                                                value=self.value_bsd)
        self.assertTrue(rel.exists())

    def test_delete_env_value(self):
        self.login_tester()

        self.client.get(self.env_value_url, {
            'a': 'remove',
            'env_value_id': self.value_linux.pk,
            'run_id': self.test_run.pk,
        })

        rel = TCMSEnvRunValueMap.objects.filter(run=self.test_run,
                                                value=self.value_linux)
        self.assertFalse(rel.exists())

    def test_delete_env_value_from_runs(self):
        self.login_tester()

        self.client.get(self.env_value_url, {
            'a': 'remove',
            'env_value_id': self.value_linux.pk,
            'run_id': [self.test_run.pk, self.test_run_1.pk],
        })

        rel = TCMSEnvRunValueMap.objects.filter(run=self.test_run,
                                                value=self.value_linux)
        self.assertFalse(rel.exists())

        rel = TCMSEnvRunValueMap.objects.filter(run=self.test_run_1,
                                                value=self.value_linux)
        self.assertFalse(rel.exists())


class TestExportTestRunCases(BaseCaseRun):
    """Test export view method to export test case runs"""

    @classmethod
    def setUpTestData(cls):
        super(TestExportTestRunCases, cls).setUpTestData()

        cls.export_url = reverse('testruns-export',
                                 args=[cls.test_run.pk])

    @patch('tcms.testruns.views.time.strftime', return_value='2017-06-17')
    def test_export_to_xml_file(self, strftime):
        response = self.client.get(self.export_url, {'format': 'xml'})
        self.assertEqual(
            'attachment; filename=tcms-testcase-runs-2017-06-17.xml',
            response['Content-Disposition'])

    @patch('tcms.testruns.views.time.strftime', return_value='2017-06-17')
    def test_export_to_csv_file(self, strftime):
        response = self.client.get(self.export_url, {'format': 'csv'})
        self.assertEqual(
            'attachment; filename=tcms-testcase-runs-2017-06-17.csv',
            response['Content-Disposition'])

    def test_export_all_case_runs_to_csv_by_default(self):
        response = self.client.get(self.export_url, {'format': 'csv'})
        self.assertEqual(self.test_run.case_run.count(),
                         # Do not count header line
                         len(response.content.strip().split(os.linesep)) - 1)

    def test_export_all_case_runs_to_xml_by_default(self):
        response = self.client.get(self.export_url, {'format': 'xml'})
        xmldoc = ElementTree.fromstring(response.content)
        case_run_nodes = xmldoc.findall('testcaserun')
        self.assertEqual(self.test_run.case_run.count(), len(case_run_nodes))


class TestBugActions(BaseCaseRun):
    """Test bug view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestBugActions, cls).setUpTestData()

        user_should_have_perm(cls.tester, 'testruns.change_testrun')
        user_should_have_perm(cls.tester, 'testcases.delete_testcasebug')

        cls.bugzilla = TestCaseBugSystem.objects.get(name='Bugzilla')
        cls.jira = TestCaseBugSystem.objects.get(name='JIRA')

        cls.case_run_bug_url = reverse('testruns-bug', args=[cls.case_run_1.pk])

        cls.bug_12345 = '12345'
        cls.jira_kiwi_100 = 'KIWI-100'
        cls.case_run_1.add_bug(cls.bug_12345, bug_system_id=cls.bugzilla.pk)
        cls.case_run_1.add_bug(cls.jira_kiwi_100, bug_system_id=cls.jira.pk)

    def test_404_if_case_run_id_not_exist(self):
        self.login_tester()
        self.case_run_bug_url = reverse('testruns-bug', args=[999])

        response = self.client.get(self.case_run_bug_url, {})
        self.assert404(response)

    def test_refuse_if_action_is_unknown(self):
        self.login_tester()

        post_data = {
            'a': 'unknown action',
            'case_run': self.case_run_1.pk,
            'case': self.case_run_1.case.pk,
            'bug_system_id': TestCaseBugSystem.objects.get(name='Bugzilla').pk,
            'bug_id': '123456',
        }

        response = self.client.get(self.case_run_bug_url, post_data)

        self.assertJsonResponse(
            response,
            {'rc': 1, 'response': 'Unrecognizable actions'})

    def test_remove_bug_from_case_run(self):
        self.login_tester()

        post_data = {
            'a': 'remove',
            'case_run': self.case_run_1.pk,
            'bug_id': self.bug_12345,
        }

        response = self.client.get(self.case_run_bug_url, post_data)

        bug_exists = TestCaseBug.objects.filter(
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
        self.login_tester()

        response = self.client.post(self.remove_case_run_url, {})

        self.assertRedirects(response,
                             reverse('testruns-get', args=[self.test_run.pk]))

    def test_ignore_non_integer_case_run_ids(self):
        self.login_tester()

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
        self.login_tester()

        expected_rest_case_runs_count = self.test_run.case_run.count() - 1

        self.client.post(self.remove_case_run_url,
                         {'case_run': [self.case_run_1.pk]})

        self.assertEqual(expected_rest_case_runs_count,
                         self.test_run.case_run.count())

    def test_redirect_to_run_if_still_case_runs_exist_after_removal(self):
        self.login_tester()

        response = self.client.post(self.remove_case_run_url,
                                    {'case_run': [self.case_run_1.pk]})

        self.assertRedirects(response,
                             reverse('testruns-get', args=[self.test_run.pk]))

    def test_redirect_to_add_case_runs_if_all_case_runs_are_removed(self):
        self.login_tester()

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
        self.login_tester()

        response = self.client.post(self.update_url, {'case_run': [self.case_run_1.pk]})

        self.assertContains(
            response,
            '1 case run(s) succeed to update')

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
        cls.new_build = TestBuildFactory(name='FastTest',
                                         product=cls.new_product)
        cls.new_version = VersionFactory(value='dev0.1',
                                         product=cls.new_product)
        cls.intern = UserFactory(username='intern',
                                 email='intern@example.com')

    def test_404_if_edit_non_existing_run(self):
        self.login_tester()

        url = reverse('testruns-edit', args=[9999])
        response = self.client.get(url)

        self.assert404(response)

    def test_edit_run(self):
        self.login_tester()

        post_data = {
            'summary': 'New run summary',
            'product': self.new_product.pk,
            'product_version': self.new_version.pk,
            'build': self.new_build.pk,
            'errata_id': '',
            'manager': self.test_run.manager.email,
            'default_tester': self.intern.email,
            'estimated_time': '3m',
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
        self.login_tester()
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
