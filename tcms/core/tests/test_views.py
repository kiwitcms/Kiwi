# -*- coding: utf-8 -*-

import json

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from django_comments.models import Comment
from six.moves import http_client

from tcms.testcases.forms import CaseAutomatedForm
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestRunFactory


class BaseCaseRun(BasePlanCase):
    """Base test case containing test run and case runs"""

    @classmethod
    def setUpTestData(cls):
        super(BaseCaseRun, cls).setUpTestData()

        cls.test_run = TestRunFactory(plan=cls.plan)
        cls.case_run_1 = TestCaseRunFactory(case=cls.case_1, run=cls.test_run)
        cls.case_run_2 = TestCaseRunFactory(case=cls.case_2, run=cls.test_run)
        cls.case_run_3 = TestCaseRunFactory(case=cls.case_3, run=cls.test_run)


class TestQuickSearch(BaseCaseRun):

    @classmethod
    def setUpTestData(cls):
        super(TestQuickSearch, cls).setUpTestData()

        cls.search_url = reverse('tcms.core.views.search')

    def test_goto_plan(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'plans', 'search_content': self.plan.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testplans.views.get', args=[self.plan.pk]),
            target_status_code=http_client.MOVED_PERMANENTLY)

    def test_goto_case(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'cases', 'search_content': self.case_1.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testcases.views.get', args=[self.case_1.pk]))

    def test_goto_run(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'runs', 'search_content': self.test_run.pk})
        self.assertRedirects(
            response,
            reverse('tcms.testruns.views.get', args=[self.test_run.pk]))

    def test_goto_plan_search(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'plans', 'search_content': 'keyword'})
        url = '{}?a=search&search=keyword'.format(reverse('tcms.testplans.views.all'))
        self.assertRedirects(response, url)

    def test_goto_case_search(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'cases', 'search_content': 'keyword'})
        url = '{}?a=search&search=keyword'.format(reverse('tcms.testcases.views.all'))
        self.assertRedirects(response, url)

    def test_goto_run_search(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'runs', 'search_content': 'keyword'})
        url = '{}?a=search&search=keyword'.format(reverse('tcms.testruns.views.all'))
        self.assertRedirects(response, url)

    def test_goto_search_if_no_object_is_found(self):
        non_existing_pk = 9999999
        response = self.client.get(self.search_url,
                                   {'search_type': 'cases', 'search_content': non_existing_pk})
        url = '{}?a=search&search={}'.format(reverse('tcms.testcases.views.all'), non_existing_pk)
        self.assertRedirects(response, url)

    def test_404_if_unknown_search_type(self):
        response = self.client.get(self.search_url,
                                   {'search_type': 'unknown type', 'search_content': self.plan.pk})
        self.assertEqual(http_client.NOT_FOUND, response.status_code)


class TestCommentCaseRuns(BaseCaseRun):
    """Test case for ajax.comment_case_runs"""

    @classmethod
    def setUpTestData(cls):
        super(TestCommentCaseRuns, cls).setUpTestData()

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')

        cls.many_comments_url = reverse('tcms.core.ajax.comment_case_runs')

    def test_refuse_if_missing_comment(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.post(self.many_comments_url,
                                    {'run': [self.case_run_1.pk, self.case_run_2.pk]})
        self.assertEqual({'rc': 1, 'response': 'Comments needed'},
                         json.loads(response.content))

    def test_refuse_if_missing_no_case_run_pk(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.post(self.many_comments_url,
                                    {'comment': 'new comment', 'run': []})
        self.assertEqual({'rc': 1, 'response': 'No runs selected.'},
                         json.loads(response.content))

        response = self.client.post(self.many_comments_url,
                                    {'comment': 'new comment'})
        self.assertEqual({'rc': 1, 'response': 'No runs selected.'},
                         json.loads(response.content))

    def test_refuse_if_passed_case_run_pks_not_exist(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.post(self.many_comments_url,
                                    {'comment': 'new comment',
                                     'run': '99999998,1009900'})
        self.assertEqual({'rc': 1, 'response': 'No caserun found.'},
                         json.loads(response.content))

    def test_add_comment_to_case_runs(self):
        self.client.login(username=self.tester.username, password='password')

        new_comment = 'new comment'
        response = self.client.post(
            self.many_comments_url,
            {'comment': new_comment,
             'run': ','.join([str(self.case_run_1.pk),
                              str(self.case_run_2.pk)])})
        self.assertEqual({'rc': 0, 'response': 'ok'},
                         json.loads(response.content))

        # Assert comments are added
        case_run_ct = ContentType.objects.get_for_model(TestCaseRun)

        for case_run_pk in (self.case_run_1.pk, self.case_run_2.pk):
            comments = Comment.objects.filter(object_pk=case_run_pk,
                                              content_type=case_run_ct)
            self.assertEqual(new_comment, comments[0].comment)
            self.assertEqual(self.tester, comments[0].user)


class TestUpdateObject(BasePlanCase):
    """Test case for update"""

    @classmethod
    def setUpTestData(cls):
        super(TestUpdateObject, cls).setUpTestData()

        cls.permission = 'testplans.change_testplan'
        cls.update_url = reverse('tcms.core.ajax.update')

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        post_data = {
            'content_type': 'testplans.testplan',
            'object_pk': self.plan.pk,
            'field': 'is_active',
            'value': 'False',
            'value_type': 'bool'
        }

        remove_perm_from_user(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.post(self.update_url, post_data)

        self.assertEqual({'rc': 1, 'response': 'Permission Dinied.'},
                         json.loads(response.content))

    def test_update_plan_is_active(self):
        post_data = {
            'content_type': 'testplans.testplan',
            'object_pk': self.plan.pk,
            'field': 'is_active',
            'value': 'False',
            'value_type': 'bool'
        }
        self.client.login(username=self.tester.username, password='password')

        response = self.client.post(self.update_url, post_data)

        self.assertEqual({'rc': 0, 'response': 'ok'}, json.loads(response.content))
        plan = TestPlan.objects.get(pk=self.plan.pk)
        self.assertFalse(plan.is_active)


class TestUpdateCaseRunStatus(BaseCaseRun):
    """Test case for update_case_run_status"""

    @classmethod
    def setUpTestData(cls):
        super(TestUpdateCaseRunStatus, cls).setUpTestData()

        cls.permission = 'testruns.change_testcaserun'
        cls.update_url = reverse('tcms.core.ajax.update_case_run_status')

        cls.tester = User.objects.create_user(username='tester',
                                              email='tester@example.com',
                                              password='password')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        self.client.login(username=self.tester.username, password='password')

        response = self.client.post(self.update_url, {
            'content_type': 'testruns.testcaserun',
            'object_pk': self.case_run_1.pk,
            'field': 'case_run_status',
            'value': str(TestCaseRunStatus.objects.get(name='PAUSED').pk),
            'value_type': 'int',
        })

        self.assertEqual({'rc': 1, 'response': 'Permission Dinied.'},
                         json.loads(response.content))

    def test_change_case_run_status(self):
        self.client.login(username=self.tester.username, password='password')

        response = self.client.post(self.update_url, {
            'content_type': 'testruns.testcaserun',
            'object_pk': self.case_run_1.pk,
            'field': 'case_run_status',
            'value': str(TestCaseRunStatus.objects.get(name='PAUSED').pk),
            'value_type': 'int',
        })

        self.assertEqual({'rc': 0, 'response': 'ok'}, json.loads(response.content))
        self.assertEqual(
            'PAUSED', TestCaseRun.objects.get(pk=self.case_run_1.pk).case_run_status.name)


class TestGetForm(TestCase):
    """Test case for form"""

    def test_get_form(self):
        response = self.client.get(reverse('tcms.core.ajax.form'),
                                   {'app_form': 'testcases.CaseAutomatedForm'})
        form = CaseAutomatedForm()
        self.assertHTMLEqual(response.content, form.as_p())
