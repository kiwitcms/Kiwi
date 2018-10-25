# -*- coding: utf-8 -*-

from http import HTTPStatus
from urllib.parse import urlencode

from django import test
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django_comments.models import Comment

from tcms.management.models import Priority
from tcms.testcases.forms import TestCase
from tcms.testruns.models import TestCaseRun
from tcms.tests import BaseCaseRun
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.tests.factories import UserFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestCaseRunFactory


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


class TestDashboard(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # used to reproduce Sentry #KIWI-TCMS-38 where rendering fails
        # with that particular value
        cls.chinese_tp = TestPlanFactory(name="缺货反馈测试需求",
                                         author=cls.tester)

    def test_when_not_logged_in_redirects_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('core-views-index'))
        self.assertRedirects(
            response,
            reverse('tcms-login')+'?next=/',
            target_status_code=HTTPStatus.OK)

    def test_when_logged_in_renders_dashboard(self):
        response = self.client.get(reverse('core-views-index'))
        self.assertContains(response, 'Test Plans')
        self.assertContains(response, 'Test Runs')

    def test_dashboard_shows_testruns_for_manager(self):
        test_run = TestRunFactory(manager=self.tester)

        response = self.client.get(reverse('core-views-index'))
        self.assertContains(response, test_run.summary)

    def test_dashboard_shows_testruns_for_default_tester(self):
        test_run = TestRunFactory(default_tester=self.tester)

        response = self.client.get(reverse('core-views-index'))
        self.assertContains(response, test_run.summary)

    def test_dashboard_shows_testruns_for_test_case_run_assignee(self):
        test_case_run = TestCaseRunFactory(assignee=self.tester)

        response = self.client.get(reverse('core-views-index'))
        self.assertContains(response, test_case_run.run.summary)


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


class TestUpdateCasePriority(BasePlanCase):
    @classmethod
    def setUpTestData(cls):
        super(TestUpdateCasePriority, cls).setUpTestData()

        cls.permission = 'testcases.change_testcase'
        cls.url = reverse('ajax.update.cases-priority')

    def setUp(self):
        user_should_have_perm(self.tester, self.permission)

    def test_refuse_if_missing_permission(self):
        remove_perm_from_user(self.tester, self.permission)
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(
            self.url,
            {
                'case[]': [self.case_1.pk, self.case_3.pk],
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
            self.url,
            {
                'case[]': [self.case_1.pk, self.case_3.pk],
                'new_value': Priority.objects.get(value='P3').pk,
            })

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok'})

        for pk in (self.case_1.pk, self.case_3.pk):
            self.assertEqual('P3', TestCase.objects.get(pk=pk).priority.value)
