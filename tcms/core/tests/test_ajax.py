# -*- coding: utf-8 -*-
from http import HTTPStatus

from django import test
from django.db.models import Count
from django.http.request import HttpRequest
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.core.ajax import _TagCounter, _TagObjects
from tcms.testcases.models import TestCase, TestCaseTag
from tcms.testplans.models import TestPlanTag
from tcms.testruns.models import TestRunTag
from tcms.tests import BasePlanCase
from tcms.tests.factories import (TagFactory, TestCaseFactory, TestPlanFactory,
                                  TestRunFactory)
from tcms.utils.permissions import initiate_user_with_default_setups


class TestTestCaseUpdates(BasePlanCase):
    """
        Tests for TC bulk update actions triggered via
        TP sub-menu.
    """
    def _assert_default_tester_is(self, expected_value):
        for test_case in TestCase.objects.filter(plan=self.plan):
            self.assertEqual(test_case.default_tester, expected_value)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.url = reverse('ajax.update.cases-actor')
        cls.case_pks = []
        for case in TestCase.objects.filter(plan=cls.plan):
            cls.case_pks.append(case.pk)

    def setUp(self):
        super().setUp()
        self._assert_default_tester_is(None)

    def test_update_default_tester_via_username(self):
        response = self.client.post(self.url, {
            'case[]': self.case_pks,
            'what_to_update': 'default_tester',
            'username': self.tester.username
        })

        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})
        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_via_email(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/85
        response = self.client.post(self.url, {
            'case[]': self.case_pks,
            'what_to_update': 'default_tester',
            'username': self.tester.email
        })

        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})
        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_non_existing_user(self):
        username = 'user which doesnt exist'
        response = self.client.post(self.url, {
            'case[]': self.case_pks,
            'what_to_update': 'default_tester',
            'username': username
        })

        self.assertJsonResponse(
            response,
            {'rc': 1, 'response': _('User %s not found!') % username},
            HTTPStatus.NOT_FOUND)
        self._assert_default_tester_is(None)


class TestTagRender(BasePlanCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse('ajax-tags')
        cls.test_tag = TagFactory()
        cls.test_plan = TestPlanFactory()
        cls.test_case = TestCaseFactory()
        cls.test_run = TestRunFactory()

        cls.test_plan.add_tag(cls.test_tag)
        cls.test_case.add_tag(cls.test_tag)
        cls.test_run.add_tag(cls.test_tag)

        for _i in range(0, 3):
            TestPlanFactory().add_tag(cls.test_tag)

        for _i in range(0, 4):
            TestCaseFactory().add_tag(cls.test_tag)

        for _i in range(0, 5):
            TestRunFactory().add_tag(cls.test_tag)

    def test_render_plan(self):
        response = self.client.get(self.url, {
            'plan': self.test_plan.pk
        })

        self._assert_tags(response)

    def _assert_tags(self, response):
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # asserting the number of tags for the given plan/case/run
        self.assertEqual(self.test_plan.tag.count(), 1)

        # asserting the number or plans/cases/runs the tag has been assigned to
        self.assertContains(response, '>4</a>')
        self.assertContains(response, '>5</a>')
        self.assertContains(response, '>6</a>')


class TestTagObjects(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.request = HttpRequest()

        cls.test_plan = TestPlanFactory()
        cls.test_case = TestCaseFactory()

    def test_get_plan(self):
        self.request.GET = {'plan': self.test_plan.pk}
        tag_objects = _TagObjects(self.request)

        self.assertEqual(tag_objects.get()[0], 'management/get_tag.html')
        self.assertEqual(tag_objects.get()[1], self.test_plan)


class TestTagCounter(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tag_one = TagFactory()
        cls.tag_two = TagFactory()
        cls.tag_three = TagFactory()
        cls.tags = [cls.tag_one, cls.tag_two, cls.tag_three]

    def test_with_empty_query(self):
        """Given an empty TestCaseTag QuerySet we expect the result of all the counting to be 0"""

        test_case_tags = TestCaseTag.objects.filter(tag=-1).values('tag').annotate(
            num_cases=Count('tag')).order_by('tag')

        case_tag_counter = _TagCounter('num_cases', test_case_tags)
        count_for_tag_one = case_tag_counter.calculate_tag_count(self.tag_one)
        count_for_tag_two = case_tag_counter.calculate_tag_count(self.tag_two)

        self.assertEqual(count_for_tag_one, 0)
        self.assertEqual(count_for_tag_two, 0)

    def test_with_tag_not_in_query(self):
        """Given a QuerySet that does not contain a given tag,the count for this tag should be 0"""

        test_case = TestCaseFactory()
        test_case.add_tag(self.tag_one)

        test_case_tags = TestCaseTag.objects.filter(
            tag=self.tag_one).values('tag').annotate(
                num_cases=Count('tag')).order_by('tag')

        case_tag_counter = _TagCounter('num_cases', test_case_tags)
        count_for_tag_one = case_tag_counter.calculate_tag_count(self.tag_one)
        count_for_tag_two = case_tag_counter.calculate_tag_count(self.tag_two)

        self.assertEqual(count_for_tag_one, 1)
        self.assertEqual(count_for_tag_two, 0)

    def test_in_loop(self):

        test_plan = TestPlanFactory()
        test_run = TestRunFactory()
        test_case_one = TestCaseFactory()
        test_case_two = TestCaseFactory()

        test_plan.add_tag(self.tag_one)
        test_plan.add_tag(self.tag_two)
        test_plan.add_tag(self.tag_three)

        test_case_one.add_tag(self.tag_one)
        test_case_one.add_tag(self.tag_three)

        test_run.add_tag(self.tag_two)

        test_case_two.add_tag(self.tag_three)

        test_plan_tags = TestPlanTag.objects.filter(tag__in=self.tags).values('tag').annotate(
            num_plans=Count('tag')).order_by('tag')
        test_case_tags = TestCaseTag.objects.filter(tag__in=self.tags).values('tag').annotate(
            num_cases=Count('tag')).order_by('tag')
        test_run_tags = TestRunTag.objects.filter(tag__in=self.tags).values('tag').annotate(
            num_runs=Count('tag')).order_by('tag')

        plan_counter = _TagCounter('num_plans', test_plan_tags)
        case_counter = _TagCounter('num_cases', test_case_tags)
        run_counter = _TagCounter('num_runs', test_run_tags)

        for tag in self.tags:
            tag.num_plans = plan_counter.calculate_tag_count(tag)
            tag.num_cases = case_counter.calculate_tag_count(tag)
            tag.num_runs = run_counter.calculate_tag_count(tag)

        self.assertEqual(self.tag_one.num_plans, 1)
        self.assertEqual(self.tag_two.num_plans, 1)
        self.assertEqual(self.tag_three.num_plans, 1)

        self.assertEqual(self.tag_one.num_cases, 1)
        self.assertEqual(self.tag_two.num_cases, 0)
        self.assertEqual(self.tag_three.num_cases, 2)

        self.assertEqual(self.tag_one.num_runs, 0)
        self.assertEqual(self.tag_two.num_runs, 1)
        self.assertEqual(self.tag_three.num_runs, 0)
