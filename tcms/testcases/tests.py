# -*- coding: utf-8 -*-

import json
import unittest

from django import test
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.test import Client

from uuslug import slugify

from fields import MultipleEmailField
from forms import CaseTagForm
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCaseBugSystem
from tcms.testcases.models import TestCaseComponent
from tcms.testcases.models import TestCasePlan
from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import TestBuildFactory
from tcms.tests.factories import TestCaseCategoryFactory
from tcms.tests.factories import TestCaseComponentFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestCaseRunFactory
from tcms.tests.factories import TestCaseTagFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TestRunFactory
from tcms.tests.factories import TestTagFactory
from tcms.tests import BasePlanCase
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm


class TestMultipleEmailField(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestMultipleEmailField, cls).setUpClass()
        cls.default_delimiter = ','
        cls.field = MultipleEmailField(delimiter=cls.default_delimiter)

    def test_to_python(self):
        value = u'zhangsan@localhost'
        pyobj = self.field.to_python(value)
        self.assertEqual(pyobj, [value])

        value = u'zhangsan@localhost,,lisi@example.com,'
        pyobj = self.field.to_python(value)
        self.assertEqual(pyobj, [u'zhangsan@localhost', u'lisi@example.com'])

        for value in ('', None, []):
            pyobj = self.field.to_python(value)
            self.assertEqual(pyobj, [])

    def test_clean(self):
        value = u'zhangsan@localhost'
        data = self.field.clean(value)
        self.assertEqual(data, [value])

        value = u'zhangsan@localhost,lisi@example.com'
        data = self.field.clean(value)
        self.assertEqual(data, [u'zhangsan@localhost', u'lisi@example.com'])

        value = u',zhangsan@localhost, ,lisi@example.com, \n'
        data = self.field.clean(value)
        self.assertEqual(data, [u'zhangsan@localhost', 'lisi@example.com'])

        value = ',zhangsan,zhangsan@localhost, \n,lisi@example.com, '
        self.assertRaises(ValidationError, self.field.clean, value)

        value = ''
        self.field.required = True
        self.assertRaises(ValidationError, self.field.clean, value)

        value = ''
        self.field.required = False
        data = self.field.clean(value)
        self.assertEqual(data, [])


class TestCaseRemoveBug(BasePlanCase):
    """Test TestCase.remove_bug"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveBug, cls).setUpTestData()
        cls.build = TestBuildFactory(product=cls.product)
        cls.test_run = TestRunFactory(product_version=cls.version, plan=cls.plan,
                                      manager=cls.tester, default_tester=cls.tester)
        cls.case_run = TestCaseRunFactory(assignee=cls.tester, tested_by=cls.tester,
                                          case=cls.case, run=cls.test_run, build=cls.build)
        cls.bug_system = TestCaseBugSystem.objects.get(name='Bugzilla')

    def setUp(self):
        self.bug_id_1 = '12345678'
        self.case.add_bug(self.bug_id_1, self.bug_system.pk,
                          summary='error when add a bug to a case')
        self.bug_id_2 = '10000'
        self.case.add_bug(self.bug_id_2, self.bug_system.pk, case_run=self.case_run)

    def tearDown(self):
        self.case.case_bug.all().delete()

    def test_remove_case_bug(self):
        self.case.remove_bug(self.bug_id_1)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertFalse(bug_found)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))

    def test_case_bug_not_removed_by_passing_case_run(self):
        self.case.remove_bug(self.bug_id_1, run_id=self.case_run.pk)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))

    def test_remove_case_run_bug(self):
        self.case.remove_bug(self.bug_id_2, run_id=self.case_run.pk)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertFalse(bug_found)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

    def test_case_run_bug_not_removed_by_missing_case_run(self):
        self.case.remove_bug(self.bug_id_2)

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_1).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_1))

        bug_found = self.case.case_bug.filter(bug_id=self.bug_id_2).exists()
        self.assertTrue(bug_found,
                        'Bug {0} does not exist. It should not be deleted.'.format(self.bug_id_2))


class TestCaseRemoveComponent(BasePlanCase):
    """Test TestCase.remove_component"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveComponent, cls).setUpTestData()

        cls.component_1 = ComponentFactory(name='Application',
                                           product=cls.product,
                                           initial_owner=cls.tester,
                                           initial_qa_contact=cls.tester)
        cls.component_2 = ComponentFactory(name='Database',
                                           product=cls.product,
                                           initial_owner=cls.tester,
                                           initial_qa_contact=cls.tester)

        cls.cc_rel_1 = TestCaseComponentFactory(case=cls.case, component=cls.component_1)
        cls.cc_rel_2 = TestCaseComponentFactory(case=cls.case, component=cls.component_2)

    def test_remove_a_component(self):
        self.case.remove_component(self.component_1)

        found = self.case.component.filter(pk=self.component_1.pk).exists()
        self.assertFalse(
            found, 'Component {0} exists. But, it should be removed.'.format(self.component_1.pk))
        found = self.case.component.filter(pk=self.component_2.pk).exists()
        self.assertTrue(
            found,
            'Component {0} does not exist. It should not be removed.'.format(self.component_2.pk))


class TestCaseRemovePlan(BasePlanCase):
    """Test TestCase.remove_plan"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemovePlan, cls).setUpTestData()

        cls.new_case = TestCaseFactory(author=cls.tester, default_tester=None, reviewer=cls.tester,
                                       plan=[cls.plan])

    def test_remove_plan(self):
        self.new_case.remove_plan(self.plan)

        found = self.plan.case.filter(pk=self.new_case.pk).exists()
        self.assertFalse(
            found, 'Case {0} should has no relationship to plan {0} now.'.format(self.new_case.pk,
                                                                                 self.plan.pk))


class TestCaseRemoveTag(BasePlanCase):
    """Test TestCase.remove_tag"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveTag, cls).setUpTestData()

        cls.tag_rhel = TestTagFactory(name='rhel')
        cls.tag_fedora = TestTagFactory(name='fedora')
        TestCaseTagFactory(case=cls.case, tag=cls.tag_rhel, user=cls.tester.pk)
        TestCaseTagFactory(case=cls.case, tag=cls.tag_fedora, user=cls.tester.pk)

    def test_remove_tag(self):
        self.case.remove_tag(self.tag_rhel)

        tag_pks = list(self.case.tag.all().values_list('pk', flat=True))
        self.assertEqual([self.tag_fedora.pk], tag_pks)


class CaseTagFormTest(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tag_1 = TestTagFactory(name='tag one')
        cls.tag_2 = TestTagFactory(name='tag two')
        cls.tag_3 = TestTagFactory(name='tag three')

        cls.cases = []
        for i in range(5):
            case = TestCaseFactory(summary='test_case_number_%d' % i)
            case.add_tag(cls.tag_1)
            if i % 2 == 0:
                case.add_tag(cls.tag_2)
            if i % 3 == 0:
                case.add_tag(cls.tag_3)
            cls.cases.append(case)

    def test_populate_from_cases_contains_all_three_tags(self):
        case_ids = [case.pk for case in self.cases]
        form = CaseTagForm()
        form.populate(case_ids=case_ids)

        self.assertEqual(3, len(form.fields['o_tag'].queryset))
        form_tags = form.fields['o_tag'].queryset.values_list('name', flat=True)
        self.assertIn(self.tag_1.name, form_tags)
        self.assertIn(self.tag_2.name, form_tags)
        self.assertIn(self.tag_3.name, form_tags)


# ### Test cases for view methods ###


class TestOperateComponentView(BasePlanCase):
    """Tests for operating components on cases"""

    @classmethod
    def setUpTestData(cls):
        super(TestOperateComponentView, cls).setUpTestData()

        cls.comp_application = ComponentFactory(name='Application',
                                                product=cls.product,
                                                initial_owner=cls.tester,
                                                initial_qa_contact=cls.tester)
        cls.comp_database = ComponentFactory(name='Database',
                                             product=cls.product,
                                             initial_owner=cls.tester,
                                             initial_qa_contact=cls.tester)
        cls.comp_cli = ComponentFactory(name='CLI',
                                        product=cls.product,
                                        initial_owner=cls.tester,
                                        initial_qa_contact=cls.tester)
        cls.comp_api = ComponentFactory(name='API',
                                        product=cls.product,
                                        initial_owner=cls.tester,
                                        initial_qa_contact=cls.tester)

        TestCaseComponentFactory(case=cls.case_1, component=cls.comp_cli)
        TestCaseComponentFactory(case=cls.case_1, component=cls.comp_api)

        cls.tester = User.objects.create(username='tester', email='tester@example.com')
        cls.tester.set_password('password')
        cls.tester.save()

        user_should_have_perm(cls.tester, 'testcases.add_testcasecomponent')

        cls.cases_component_url = reverse('tcms.testcases.views.component')

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.tester.username, password='password')

    def tearDown(self):
        self.client.logout()

        remove_perm_from_user(self.tester, 'testcases.delete_testcasecomponent')

    def test_show_components_form(self):
        response = self.client.post(self.cases_component_url,
                                    {'product': self.product.pk})

        self.assertContains(
            response,
            '<option value="{}" selected="selected">{}</option>'.format(
                self.product.pk, self.product.name),
            html=True)

        comp_options = ('<option value="{}">{}</option>'.format(comp.pk, comp.name)
                        for comp in (self.comp_application, self.comp_database,
                                     self.comp_cli, self.comp_api))
        self.assertContains(
            response,
            '''<select multiple="multiple" id="id_o_component" name="o_component">
{}
</select>'''.format(''.join(comp_options)),
            html=True)

    def test_add_components(self):
        post_data = {
            'product': self.product.pk,
            'o_component': [self.comp_application.pk, self.comp_database.pk],
            'case': [self.case_1.pk],
            'a': 'add',
            'from_plan': self.plan.pk,
        }
        response = self.client.post(self.cases_component_url, post_data)

        data = json.loads(response.content)
        self.assertEqual({'rc': 0, 'response': 'ok', 'errors_list': []}, data)

        for comp in (self.comp_application, self.comp_database):
            has_comp = TestCaseComponent.objects.filter(case=self.case_1, component=comp).exists()
            self.assertTrue(has_comp)

    def test_missing_delete_perm(self):
        post_data = {
            'o_component': [self.comp_cli.pk, self.comp_api.pk],
            'case': [self.case_1.pk],
            'a': 'remove',
        }
        response = self.client.post(self.cases_component_url, post_data)
        data = json.loads(response.content)
        self.assertEqual(
            {'rc': 1, 'response': 'Permission denied - delete', 'errors_list': []},
            data)

    def test_remove_components(self):
        user_should_have_perm(self.tester, 'testcases.delete_testcasecomponent')

        post_data = {
            'o_component': [self.comp_cli.pk, self.comp_api.pk],
            'case': [self.case_1.pk],
            'a': 'remove',
        }
        response = self.client.post(self.cases_component_url, post_data)

        data = json.loads(response.content)
        self.assertEqual({'rc': 0, 'response': 'ok', 'errors_list': []}, data)

        for comp in (self.comp_cli, self.comp_api):
            has_comp = TestCaseComponent.objects.filter(case=self.case_1, component=comp).exists()
            self.assertFalse(has_comp)


class TestOperateCategoryView(BasePlanCase):
    """Tests for operating category on cases"""

    @classmethod
    def setUpTestData(cls):
        super(TestOperateCategoryView, cls).setUpTestData()

        cls.case_cat_full_auto = TestCaseCategoryFactory(name='Full Auto', product=cls.product)
        cls.case_cat_full_manual = TestCaseCategoryFactory(name='Full Manual', product=cls.product)

        cls.tester = User.objects.create(username='tester', email='tester@example.com')
        cls.tester.set_password('password')
        cls.tester.save()

        user_should_have_perm(cls.tester, 'testcases.add_testcasecomponent')

        cls.case_category_url = reverse('tcms.testcases.views.category')

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.tester.username, password='password')

    def tearDown(self):
        self.client.logout()

    def test_show_categories_form(self):
        response = self.client.post(self.case_category_url, {'product': self.product.pk})

        self.assertContains(
            response,
            '<option value="{}" selected="selected">{}</option>'.format(
                self.product.pk, self.product.name),
            html=True)

        categories = ('<option value="{}">{}</option>'.format(category.pk, category.name)
                      for category in self.product.category.all())
        self.assertContains(
            response,
            '''<select multiple="multiple" id="id_o_category" name="o_category">
{}
</select>'''.format(''.join(categories)),
            html=True)

    def test_update_cases_category(self):
        post_data = {
            'from_plan': self.plan.pk,
            'product': self.product.pk,
            'case': [self.case_1.pk, self.case_3.pk],
            'a': 'update',
            'o_category': self.case_cat_full_auto.pk,
        }
        response = self.client.post(self.case_category_url, post_data)

        data = json.loads(response.content)
        self.assertEqual({'rc': 0, 'response': 'ok', 'errors_list': []}, data)

        for pk in (self.case_1.pk, self.case_3.pk):
            case = TestCase.objects.get(pk=pk)
            self.assertEqual(self.case_cat_full_auto, case.category)


class TestAddIssueToCase(BasePlanCase):
    """Tests for adding issue to case"""

    @classmethod
    def setUpTestData(cls):
        super(TestAddIssueToCase, cls).setUpTestData()

        cls.plan_tester = User.objects.create_user(username='plantester',
                                                   email='plantester@example.com',
                                                   password='password')
        user_should_have_perm(cls.plan_tester, 'testcases.change_testcasebug')

        cls.case_bug_url = reverse('tcms.testcases.views.bug', args=[cls.case_1.pk])
        cls.issue_tracker = TestCaseBugSystem.objects.get(name='Bugzilla')

    def test_add_and_remove_a_bug(self):
        user_should_have_perm(self.plan_tester, 'testcases.add_testcasebug')
        user_should_have_perm(self.plan_tester, 'testcases.delete_testcasebug')

        self.client.login(username=self.plan_tester.username, password='password')
        request_data = {
            'handle': 'add',
            'case': self.case_1.pk,
            'bug_id': '123456',
            'bug_system': self.issue_tracker.pk,
        }
        self.client.get(self.case_bug_url, request_data)
        self.assertTrue(self.case_1.case_bug.filter(bug_id='123456').exists())

        request_data = {
            'handle': 'remove',
            'case': self.case_1.pk,
            'bug_id': '123456',
        }
        self.client.get(self.case_bug_url, request_data)

        not_have_bug = self.case_1.case_bug.filter(bug_id='123456').exists()
        self.assertTrue(not_have_bug)


class TestOperateCasePlans(BasePlanCase):
    """Test operation in case' plans tab"""

    @classmethod
    def setUpTestData(cls):
        super(TestOperateCasePlans, cls).setUpTestData()

        # Besides the plan and its cases created in parent class, this test case
        # also needs other cases in order to list multiple plans of a case and
        # remove a plan from a case.

        cls.plan_test_case_plans = TestPlanFactory(author=cls.tester,
                                                   owner=cls.tester,
                                                   product=cls.product,
                                                   product_version=cls.version)
        cls.plan_test_add = TestPlanFactory(author=cls.tester,
                                            owner=cls.tester,
                                            product=cls.product,
                                            product_version=cls.version)
        cls.plan_test_remove = TestPlanFactory(author=cls.tester,
                                               owner=cls.tester,
                                               product=cls.product,
                                               product_version=cls.version)

        cls.case_1.add_to_plan(cls.plan_test_case_plans)
        cls.case_1.add_to_plan(cls.plan_test_remove)

        cls.plan_tester = User.objects.create_user(username='plantester',
                                                   email='plantester@example.com',
                                                   password='password')

        cls.case_plans_url = reverse('tcms.testcases.views.plan', args=[cls.case_1.pk])

    def tearDown(self):
        remove_perm_from_user(self.plan_tester, 'testcases.add_testcaseplan')
        remove_perm_from_user(self.plan_tester, 'testcases.change_testcaseplan')

    def assert_list_case_plans(self, response, case):
        for case_plan_rel in TestCasePlan.objects.filter(case=case):
            plan = case_plan_rel.plan
            self.assertContains(
                response,
                '<a href="/plan/{0}/{1}">{0}</a>'.format(plan.pk, slugify(plan.name)),
                html=True)

            self.assertContains(
                response,
                '<a href="/plan/{}/{}">{}</a>'.format(plan.pk, slugify(plan.name), plan.name),
                html=True)

    def test_list_plans(self):
        response = self.client.get(self.case_plans_url)
        self.assert_list_case_plans(response, self.case_1)

    def test_missing_permission_to_add(self):
        response = self.client.get(self.case_plans_url,
                                   {'a': 'add', 'plan_id': self.plan_test_add.pk})
        self.assertContains(response, 'Permission denied')

    def test_missing_permission_to_remove(self):
        response = self.client.get(self.case_plans_url,
                                   {'a': 'remove', 'plan_id': self.plan_test_remove.pk})
        self.assertContains(response, 'Permission denied')

    def test_add_a_plan(self):
        user_should_have_perm(self.plan_tester, 'testcases.add_testcaseplan')
        self.client.login(username=self.plan_tester.username, password='password')
        response = self.client.get(self.case_plans_url,
                                   {'a': 'add', 'plan_id': self.plan_test_add.pk})

        self.assert_list_case_plans(response, self.case_1)

        self.assertTrue(TestCasePlan.objects.filter(
            plan=self.plan_test_add, case=self.case_1).exists())

    def test_remove_a_plan(self):
        user_should_have_perm(self.plan_tester, 'testcases.change_testcaseplan')
        self.client.login(username=self.plan_tester.username, password='password')
        response = self.client.get(self.case_plans_url,
                                   {'a': 'remove', 'plan_id': self.plan_test_remove.pk})

        self.assert_list_case_plans(response, self.case_1)

        not_linked_to_plan = not TestCasePlan.objects.filter(
            case=self.case_1, plan=self.plan_test_remove).exists()
        self.assertTrue(not_linked_to_plan)

    def test_add_a_few_plans(self):
        user_should_have_perm(self.plan_tester, 'testcases.add_testcaseplan')
        self.client.login(username=self.plan_tester.username, password='password')
        # This time, add a few plans to another case
        url = reverse('tcms.testcases.views.plan', args=[self.case_2.pk])

        response = self.client.get(url,
                                   {'a': 'add', 'plan_id': [self.plan_test_add.pk,
                                                            self.plan_test_remove.pk]})

        self.assert_list_case_plans(response, self.case_2)

        self.assertTrue(TestCasePlan.objects.filter(
            case=self.case_2, plan=self.plan_test_add).exists())
        self.assertTrue(TestCasePlan.objects.filter(
            case=self.case_2, plan=self.plan_test_remove).exists())
