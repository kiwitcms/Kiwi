# -*- coding: utf-8 -*-
import json
from http import HTTPStatus

from django import test
from django.urls import reverse
from django.conf import settings
from django.db.models import Count
from django.http.request import HttpRequest

from tcms.core.ajax import _TagCounter, _TagActions, _TagObjects, _InfoObjects
from tcms.testplans.models import TestPlanTag
from tcms.testruns.models import TestRunTag
from tcms.testcases.models import TestCase, TestCaseTag, Category
from tcms.tests import BasePlanCase
from tcms.management.models import Tag

from tcms.tests.factories import TagFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import CategoryFactory
from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import EnvGroupFactory
from tcms.tests.factories import EnvPropertyFactory
from tcms.tests.factories import EnvGroupPropertyMapFactory
from tcms.tests.factories import ProductFactory
from tcms.tests.factories import EnvValueFactory
from tcms.tests.factories import UserFactory
from tcms.tests.factories import VersionFactory
from tcms.tests.factories import BuildFactory

from tcms.core.contrib.auth.backends import initiate_user_with_default_setups


class TestInfo(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()

        cls.default_category = Category.objects.get(name='--default--')
        cls.category_one = CategoryFactory(product=cls.product)
        cls.category_two = CategoryFactory(product=cls.product)

        cls.categories = [cls.default_category, cls.category_one, cls.category_two]

    def test_lowercase_string_is_converted_to_bool(self):
        url = "%s?info_type=builds&product_id=1&is_active=true" % reverse('ajax-info')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_empty_string_is_converted_to_bool(self):
        url = "%s?info_type=builds&product_id=1&is_active=" % reverse('ajax-info')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)

    def test_with_unrecognisable_info_type(self):
        """ When a request comes with invalid info_type,
            we expect to receive response containing the 'Unrecognizable info-type' error message
        """

        url = "%s?info_type=INVALID" % reverse('ajax-info')

        response = self.client.get(url)

        self.assertContains(response, 'Unrecognizable info-type')

    def test_with_json_format(self):
        """ When a request comes with info_type=categories for given product_id,
            we expect to receive all categories for that product as array of JSON objects """

        url = "%s?info_type=categories&product_id=%d" % (reverse('ajax-info'), self.product.pk)

        response = self.client.get(url)
        actual_response = json.loads(response.content, encoding=settings.DEFAULT_CHARSET)

        for category in self.categories:
            expected = {"model": "testcases.category", "pk": category.pk,
                        "fields": {"name": category.name}}
            self.assertIn(expected, actual_response)


class Test_InfoObjects(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()
        cls.request = HttpRequest()

        cls.info_objects = _InfoObjects(cls.request, cls.product.pk)

        cls.build_one = BuildFactory(product=cls.product)
        cls.build_two = BuildFactory(product=cls.product)
        cls.build_two.is_active = False
        cls.build_two.save()

        cls.category_one = CategoryFactory(product=cls.product)
        cls.category_two = CategoryFactory(product=cls.product)
        cls.category_three = CategoryFactory()

        cls.component_one = ComponentFactory(product=cls.product)
        cls.component_two = ComponentFactory(product=cls.product)
        cls.component_three = ComponentFactory()

        cls.env_group_one = EnvGroupFactory()
        cls.env_group_two = EnvGroupFactory()

        cls.env_property_one = EnvPropertyFactory()
        cls.env_property_two = EnvPropertyFactory()
        EnvGroupPropertyMapFactory(group=cls.env_group_one, property=cls.env_property_one)

        cls.env_value_one = EnvValueFactory(property=cls.env_property_one)
        cls.env_value_two = EnvValueFactory()

        cls.user_one = UserFactory()
        cls.user_two = UserFactory()

        cls.version_one = VersionFactory(product=cls.product)
        cls.version_two = VersionFactory()

    def test_active_builds(self):
        self.request.GET = {'is_active': 'True'}

        info_objects = _InfoObjects(self.request, self.product.pk)
        builds = info_objects.builds()

        self.assertIn(self.build_one, builds)
        self.assertNotIn(self.build_two, builds)

    def test_non_active_builds(self):
        self.request.GET = {'is_active': 'False'}

        info_objects = _InfoObjects(self.request, self.product.pk)
        builds = info_objects.builds()

        self.assertIn(self.build_two, builds)
        self.assertNotIn(self.build_one, builds)

    def test_categories(self):

        categories = self.info_objects.categories()

        self.assertIn(self.category_one, categories)
        self.assertIn(self.category_two, categories)
        self.assertNotIn(self.category_three, categories)

    def test_components(self):

        components = self.info_objects.components()

        self.assertIn(self.component_one, components)
        self.assertIn(self.component_two, components)
        self.assertNotIn(self.component_three, components)

    def test_env_groups(self):

        env_groups = self.info_objects.env_groups()

        self.assertIn(self.env_group_one, env_groups)
        self.assertIn(self.env_group_two, env_groups)

    def test_env_properties(self):

        env_properties = self.info_objects.env_properties()

        self.assertIn(self.env_property_one, env_properties)
        self.assertIn(self.env_property_two, env_properties)

    def test_env_properties_by_env_group(self):
        self.request.GET = {'env_group_id': self.env_group_one.pk}

        info_objects = _InfoObjects(self.request)
        env_properties = info_objects.env_properties()

        self.assertIn(self.env_property_one, env_properties)
        self.assertNotIn(self.env_property_two, env_properties)

    def test_env_values(self):
        self.request.GET = {'env_property_id': self.env_property_one.pk}

        info_objects = _InfoObjects(self.request)
        env_values = info_objects.env_values()

        self.assertIn(self.env_value_one, env_values)
        self.assertNotIn(self.env_value_two, env_values)

    def test_users(self):
        self.request.GET = {'username': self.user_one.username}

        info_objects = _InfoObjects(self.request)
        users = info_objects.users()

        self.assertIn(self.user_one, users)
        self.assertNotIn(self.user_two, users)

    def test_version(self):

        test_versions = self.info_objects.versions()

        self.assertIn(self.version_one, test_versions)
        self.assertNotIn(self.version_two, test_versions)


class Test_TestCaseUpdates(BasePlanCase):
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

    def setUp(self):
        super().setUp()
        self._assert_default_tester_is(None)

    def test_update_default_tester_via_username(self):
        response = self.client.post(self.url, {
            'case[]': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'what_to_update': 'default_tester',
            'username': self.tester.username
        })

        self.assertEqual(HTTPStatus.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')

        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_via_email(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/85
        response = self.client.post(self.url, {
            'case[]': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'what_to_update': 'default_tester',
            'username': self.tester.email
        })

        self.assertEqual(HTTPStatus.OK, response.status_code)
        result = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))
        self.assertEqual(result['rc'], 0)
        self.assertEqual(result['response'], 'ok')

        self._assert_default_tester_is(self.tester)

    def test_update_default_tester_non_existing_user(self):
        response = self.client.post(self.url, {
            'case[]': [case.pk for case in TestCase.objects.filter(plan=self.plan)],
            'what_to_update': 'default_tester',
            'usernmae': 'user which doesnt exist'
        })

        self.assertEqual(HTTPStatus.OK, response.status_code)
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

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.test_plan.tag.count(), 1)
        self.assertTrue(self.test_tag in self.test_plan.tag.all())

    def test_add_tag_to_test_case(self):
        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'case': self.test_case.case_id,
            'a': 'add'
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.test_case.tag.count(), 1)
        self.assertTrue(self.test_tag in self.test_case.tag.all())

    def test_add_tag_to_test_run(self):
        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'run': self.test_run.run_id,
            'a': 'add'
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
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

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.test_plan.tag.count(), 0)

    def test_remove_tag_from_test_case(self):
        self.test_case.add_tag(self.test_tag)

        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'case': self.test_case.case_id,
            'a': 'remove'
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(self.test_case.tag.count(), 0)

    def test_remove_tag_from_test_run(self):
        self.test_run.add_tag(self.test_tag)

        response = self.client.get(self.url, {
            'tags': self.test_tag,
            'run': self.test_run.run_id,
            'a': 'remove'
        })

        self.assertEqual(response.status_code, HTTPStatus.OK)
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
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # asserting the number of tags for the given plan/case/run
        self.assertEqual(self.test_plan.tag.count(), 1)
        self.assertEqual(self.test_case.tag.count(), 1)
        self.assertEqual(self.test_run.tag.count(), 1)

        # asserting the number or plans/cases/runs the tag has been assigned to
        self.assertContains(response, '>4</a>')
        self.assertContains(response, '>5</a>')
        self.assertContains(response, '>6</a>')


class Test_Tag_Objects(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.request = HttpRequest()

        cls.test_plan = TestPlanFactory()
        cls.test_case = TestCaseFactory()
        cls.test_run = TestRunFactory()

    def test_get_plan(self):
        self.request.GET = {'plan': self.test_plan.pk}
        tag_objects = _TagObjects(self.request)

        self.assertEqual(tag_objects.get()[0], 'management/get_tag.html')
        self.assertEqual(tag_objects.get()[1], self.test_plan)

    def test_get_case(self):
        self.request.GET = {'case': self.test_case.pk}
        tag_objects = _TagObjects(self.request)

        self.assertEqual(tag_objects.get()[0], 'management/get_tag.html')
        self.assertEqual(tag_objects.get()[1], self.test_case)

    def test_get_run(self):
        self.request.GET = {'run': self.test_run.pk}
        tag_objects = _TagObjects(self.request)

        self.assertEqual(tag_objects.get()[0], 'run/get_tag.html')
        self.assertEqual(tag_objects.get()[1], self.test_run)


class Test_Tag_Actions(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.test_plan = TestPlanFactory()
        cls.test_case = TestCaseFactory()
        cls.test_run = TestRunFactory()

        cls.tag = TagFactory()

        cls.test_run.add_tag(cls.tag)

    def test_add_tag_to_obj(self):
        tag_actions = _TagActions(self.test_plan, self.tag.name)
        tag_actions.add()

        self.assertEqual(TestPlanTag.objects.filter(plan=self.test_plan).count(), 1)

    def test_create_tag_and_add_to_obj(self):
        tag_actions = _TagActions(self.test_case, 'tag_name')
        tag_actions.add()

        self.assertEqual(Tag.objects.filter(name='tag_name').count(), 1)
        self.assertEqual(TestCaseTag.objects.filter(case=self.test_case).count(), 1)

    def test_remove_tag_from_obj(self):
        tag_actions = _TagActions(self.test_run, self.tag.name)
        tag_actions.remove()

        self.assertEqual(Tag.objects.filter(name=self.tag.name).count(), 1)
        self.assertEqual(TestRunTag.objects.filter(run=self.test_run).count(), 0)


class Test_Tag_Counter(test.TestCase):

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
