# -*- coding: utf-8 -*-

import json
from http import HTTPStatus
from urllib.parse import urlencode

from django import test
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.urls import reverse
from django_comments.models import Comment

from tcms.management.models import Priority
from tcms.management.models import EnvGroup
from tcms.management.models import EnvProperty
from tcms.testcases.forms import TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.tests import BaseCaseRun
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import UserFactory
from tcms.tests.factories import EnvGroupFactory
from tcms.tests.factories import EnvGroupPropertyMapFactory
from tcms.tests.factories import EnvPropertyFactory


class TestNavigation(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        super(TestNavigation, cls).setUpTestData()
        cls.user = UserFactory(email='user+1@example.com')
        cls.user.set_password('testing')
        cls.user.save()

    def test_urls_for_emails_with_pluses(self):
        # test for https://github.com/Nitrate/Nitrate/issues/262
        # when email contains + sign it needs to be properly urlencoded
        # before passing it as query string argument to the search views
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.user.username,
            password='testing')
        response = self.client.get(reverse('iframe-navigation'))

        self.assertContains(response, urlencode({'people': self.user.email}))
        self.assertContains(response, urlencode({'author__email__startswith': self.user.email}))


class TestIndex(BaseCaseRun):
    def test_when_not_logged_in_index_page_redirects_to_login(self):
        response = self.client.get(reverse('core-views-index'))
        self.assertRedirects(
            response,
            reverse('tcms-login'),
            target_status_code=HTTPStatus.OK)

    def test_when_logged_in_index_page_redirects_to_dashboard(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')
        response = self.client.get(reverse('core-views-index'))
        self.assertRedirects(
            response,
            reverse('tcms-recent', args=[self.tester.username]),
            target_status_code=HTTPStatus.OK)


class TestCommentCaseRuns(BaseCaseRun):
    """Test case for ajax.comment_case_runs"""

    @classmethod
    def setUpTestData(cls):
        super(TestCommentCaseRuns, cls).setUpTestData()
        cls.many_comments_url = reverse('ajax-comment_case_runs')

    def test_refuse_if_missing_comment(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(self.many_comments_url,
                                    {'run': [self.case_run_1.pk, self.case_run_2.pk]})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Comments needed'})

    def test_refuse_if_missing_no_case_run_pk(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(self.many_comments_url,
                                    {'comment': 'new comment', 'run': []})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'No runs selected.'})

        response = self.client.post(self.many_comments_url,
                                    {'comment': 'new comment'})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'No runs selected.'})

    def test_refuse_if_passed_case_run_pks_not_exist(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(self.many_comments_url,
                                    {'comment': 'new comment',
                                     'run': '99999998,1009900'})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'No caserun found.'})

    def test_add_comment_to_case_runs(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        new_comment = 'new comment'
        response = self.client.post(
            self.many_comments_url,
            {'comment': new_comment,
             'run': ','.join([str(self.case_run_1.pk),
                              str(self.case_run_2.pk)])})
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})

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
        cls.update_url = reverse('ajax-update')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        remove_perm_from_user(self.tester, self.permission)

        post_data = {
            'content_type': 'testplans.testplan',
            'object_pk': self.plan.pk,
            'field': 'is_active',
            'value': 'False',
            'value_type': 'bool'
        }

        response = self.client.post(self.update_url, post_data)

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission Dinied.'})

    def test_update_plan_is_active(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        post_data = {
            'content_type': 'testplans.testplan',
            'object_pk': self.plan.pk,
            'field': 'is_active',
            'value': 'False',
            'value_type': 'bool'
        }

        response = self.client.post(self.update_url, post_data)

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})
        plan = TestPlan.objects.get(pk=self.plan.pk)
        self.assertFalse(plan.is_active)


class TestUpdateCaseRunStatus(BaseCaseRun):
    """Test case for update_case_run_status"""

    @classmethod
    def setUpTestData(cls):
        super(TestUpdateCaseRunStatus, cls).setUpTestData()

        cls.permission = 'testruns.change_testcaserun'
        cls.update_url = reverse('ajax-update_case_run_status')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(self.update_url, {
            'content_type': 'testruns.testcaserun',
            'object_pk': self.case_run_1.pk,
            'field': 'case_run_status',
            'value': str(TestCaseRunStatus.objects.get(name='PAUSED').pk),
            'value_type': 'int',
        })

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission Dinied.'})

    def test_change_case_run_status(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(self.update_url, {
            'content_type': 'testruns.testcaserun',
            'object_pk': self.case_run_1.pk,
            'field': 'case_run_status',
            'value': str(TestCaseRunStatus.objects.get(name='PAUSED').pk),
            'value_type': 'int',
        })

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})
        self.assertEqual(
            'PAUSED', TestCaseRun.objects.get(pk=self.case_run_1.pk).case_run_status.name)


class TestUpdateCasePriority(BasePlanCase):
    """Test case for update_cases_default_tester"""

    @classmethod
    def setUpTestData(cls):
        super(TestUpdateCasePriority, cls).setUpTestData()

        cls.permission = 'testcases.change_testcase'
        cls.case_update_url = reverse('ajax-update_cases_default_tester')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(
            self.case_update_url,
            {
                'target_field': 'priority',
                'from_plan': self.plan.pk,
                'case': [self.case_1.pk, self.case_3.pk],
                'new_value': Priority.objects.get(value='P3').pk,
            })

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': "You don't have enough permission to "
                                  "update TestCases."})

    def test_update_case_priority(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(
            self.case_update_url,
            {
                'target_field': 'priority',
                'from_plan': self.plan.pk,
                'case': [self.case_1.pk, self.case_3.pk],
                'new_value': Priority.objects.get(value='P3').pk,
            })

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})

        for pk in (self.case_1.pk, self.case_3.pk):
            self.assertEqual('P3', TestCase.objects.get(pk=pk).priority.value)


class TestGetObjectInfo(BasePlanCase):
    """Test case for info view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetObjectInfo, cls).setUpTestData()

        cls.get_info_url = reverse('ajax-info')

        cls.group_nitrate = EnvGroupFactory(name='nitrate')
        cls.group_new = EnvGroupFactory(name='NewGroup')

        cls.property_os = EnvPropertyFactory(name='os')
        cls.property_python = EnvPropertyFactory(name='python')
        cls.property_django = EnvPropertyFactory(name='django')

        EnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                   property=cls.property_os)
        EnvGroupPropertyMapFactory(group=cls.group_nitrate,
                                   property=cls.property_python)
        EnvGroupPropertyMapFactory(group=cls.group_new,
                                   property=cls.property_django)

    def test_get_env_properties(self):
        response = self.client.get(self.get_info_url, {'info_type': 'env_properties'})

        expected_json = json.loads(
            serializers.serialize(
                'json',
                EnvProperty.objects.all(),
                fields=('name', 'value')))
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            expected_json)

    def test_get_env_properties_by_group(self):
        response = self.client.get(self.get_info_url,
                                   {'info_type': 'env_properties',
                                    'env_group_id': self.group_new.pk})

        group = EnvGroup.objects.get(pk=self.group_new.pk)
        expected_json = json.loads(
            serializers.serialize(
                'json',
                group.property.all(),
                fields=('name', 'value')))
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            expected_json)
