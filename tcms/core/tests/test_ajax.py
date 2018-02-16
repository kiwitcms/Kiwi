# -*- coding: utf-8 -*-
import json
import http.client

from django import test
from django.urls import reverse
from django.conf import settings

from tcms.testcases.models import TestCase
from tcms.tests import BasePlanCase

from tcms.tests.factories import TagFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory

from tcms.core.contrib.auth.backends import initiate_user_with_default_setups


class TestInfo(test.TestCase):

    def test_lowercase_string_is_converted_to_bool(self):
        url = "%s?info_type=builds&product_id=1&is_active=true" % reverse('ajax-info')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_empty_string_is_converted_to_bool(self):
        url = "%s?info_type=builds&product_id=1&is_active=" % reverse('ajax-info')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)


class Test_TestCaseUpdateActions(BasePlanCase):
    """
        Tests for TC bulk update actions triggered via
        TP sub-menu.
    """
    def _assert_default_tester_is(self, expected_value):
        for test_case in TestCase.objects.filter(plan=self.plan):
            self.assertEqual(test_case.default_tester, expected_value)

    @classmethod
    def setUpTestData(cls):
        super(Test_TestCaseUpdateActions, cls).setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def setUp(self):
        self.login_tester()
        self._assert_default_tester_is(None)

    def test_update_default_tester_via_username(self):
        url = reverse('ajax-update_cases_default_tester')
        response = self.client.post(url, {
            'from_plan': self.plan.pk,
            'case': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'target_field': 'default_tester',
            'new_value': self.tester.username
        })

        self.assertEqual(http.client.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')

        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_via_email(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/85
        url = reverse('ajax-update_cases_default_tester')
        response = self.client.post(url, {
            'from_plan': self.plan.pk,
            'case': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'target_field': 'default_tester',
            'new_value': self.tester.email
        })

        self.assertEqual(http.client.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')

        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_non_existing_user(self):
        url = reverse('ajax-update_cases_default_tester')
        response = self.client.post(url, {
            'from_plan': self.plan.pk,
            'case': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'target_field': 'default_tester',
            'new_value': 'user which doesnt exist'
        })

        self.assertEqual(http.client.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 1)
        self.assertEqual(result['response'], 'Default tester not found!')

        self._assert_default_tester_is(None)


class Test_Tag_Test(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('ajax-tags')
        cls.test_tag = TagFactory()
        cls.test_plan = TestPlanFactory()
        cls.test_case = TestCaseFactory()
        cls.test_run = TestRunFactory()


class Test_Tag_Add(Test_Tag_Test):

    def test_add_tag_to_test_plan(self):
        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'plan': self.test_plan.plan_id,
            'a': 'add'
        })

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(self.test_plan.tag.count(), 1)
        self.assertTrue(self.test_tag in self.test_plan.tag.all())

    def test_add_tag_to_test_case(self):
        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'case': self.test_case.case_id,
            'a': 'add'
        })

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(self.test_case.tag.count(), 1)
        self.assertTrue(self.test_tag in self.test_case.tag.all())

    def test_add_tag_to_test_run(self):
        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'run': self.test_run.run_id,
            'a': 'add'
        })

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(self.test_run.tag.count(), 1)
        self.assertTrue(self.test_tag in self.test_run.tag.all())


class Test_Tag_Remove(Test_Tag_Test):

    def test_remove_tag_from_test_plan(self):
        self.test_plan.add_tag(self.test_tag)

        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'plan': self.test_plan.plan_id,
            'a': 'remove'
        })

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(self.test_plan.tag.count(), 0)

    def test_remove_tag_from_test_case(self):
        self.test_case.add_tag(self.test_tag)

        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'case': self.test_case.case_id,
            'a': 'remove'
        })

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(self.test_case.tag.count(), 0)

    def test_remove_tag_from_test_run(self):
        self.test_run.add_tag(self.test_tag)

        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'run': self.test_run.run_id,
            'a': 'remove'
        })

        self.assertEqual(response.status_code, http.client.OK)
        self.assertEqual(self.test_run.tag.count(), 0)


class Test_Tag_Render(Test_Tag_Test):

    @classmethod
    def setUpTestData(cls):
        super(Test_Tag_Render, cls).setUpTestData()

        cls.test_plan.add_tag(cls.test_tag)
        cls.test_case.add_tag(cls.test_tag)
        cls.test_run.add_tag(cls.test_tag)

        for _ in range(0, 3):
            TestPlanFactory().add_tag(cls.test_tag)

        for _ in range(0, 4):
            TestCaseFactory().add_tag(cls.test_tag)

        for _ in range(0, 5):
            TestRunFactory().add_tag(cls.test_tag)

    def test_render_plan(self):
        response = self.client.get(self.url, {
            'plan': self.test_plan.plan_id
        })

        self._assert_tags(response)

    def test_render_case(self):
        response = self.client.get(self.url, {
            'case': self.test_case.case_id
        })

        self._assert_tags(response)

    def _assert_tags(self, response):
        self.assertEqual(response.status_code, http.client.OK)

        # asserting the number of tags for the given plan/case/run
        self.assertEqual(self.test_plan.tag.count(), 1)
        self.assertEqual(self.test_case.tag.count(), 1)
        self.assertEqual(self.test_run.tag.count(), 1)

        # asserting the number or plans/cases/runs the tag has been assigned to
        self.assertContains(response, '>4</a>')
        self.assertContains(response, '>5</a>')
        self.assertContains(response, '>6</a>')
