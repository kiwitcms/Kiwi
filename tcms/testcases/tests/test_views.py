# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

import json
import unittest
from http import HTTPStatus
import xml.etree.ElementTree  # nosec:B405:blacklist
from datetime import datetime
from urllib.parse import urlencode

from django import test
from django.contrib.auth.models import User
from django.urls import reverse
from django.conf import settings
from django.forms import ValidationError
from django.test import RequestFactory

from tcms.testcases.fields import MultipleEmailField
from tcms.testcases.forms import CaseTagForm
from tcms.management.models import Tag
from tcms.testcases.models import TestCase
from tcms.testcases.models import BugSystem
from tcms.testcases.models import TestCaseComponent
from tcms.testcases.models import TestCasePlan
from tcms.testcases.views import ajax_response
from tcms.testruns.models import TestCaseRunStatus
from tcms.tests.factories import ComponentFactory
from tcms.tests.factories import CategoryFactory
from tcms.tests.factories import TestCaseComponentFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests.factories import TestPlanFactory
from tcms.tests.factories import TagFactory
from tcms.tests import BasePlanCase, BaseCaseRun
from tcms.tests import remove_perm_from_user
from tcms.tests import user_should_have_perm
from tcms.core.contrib.auth.backends import initiate_user_with_default_setups


class TestGetCaseRunDetailsAsDefaultUser(BaseCaseRun):
    """Assert what a default user (non-admin) will see"""

    @classmethod
    def setUpTestData(cls):
        super(TestGetCaseRunDetailsAsDefaultUser, cls).setUpTestData()

    def test_user_in_default_group_sees_comments(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/74
        initiate_user_with_default_setups(self.tester)

        url = reverse('caserun-detail-pane', args=[self.case_run_1.case_id])
        response = self.client.get(
            url,
            {
                'case_run_id': self.case_run_1.pk,
                'case_text_version': self.case_run_1.case.latest_text_version()
            }
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)

        self.assertContains(
            response,
            '<textarea name="comment" cols="40" id="id_comment" maxlength="10000" '
            'rows="10">\n</textarea>',
            html=True)

        for status in TestCaseRunStatus.objects.all():
            self.assertContains(
                response,
                "<input type=\"submit\" class=\"btn btn_%s btn_status js-status-button\" "
                "title=\"%s\"" % (status.name.lower(), status.name),
                html=False
            )


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


class CaseTagFormTest(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.tag_1 = TagFactory(name='tag one')
        cls.tag_2 = TagFactory(name='tag two')
        cls.tag_3 = TagFactory(name='tag three')

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

        user_should_have_perm(cls.tester, 'testcases.add_testcasecomponent')

        cls.cases_component_url = reverse('testcases-component')

    def tearDown(self):
        remove_perm_from_user(self.tester, 'testcases.delete_testcasecomponent')

    def test_show_components_form(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        response = self.client.post(self.cases_component_url,
                                    {'product': self.product.pk})

        self.assertContains(
            response,
            '<option value="{}" selected="selected">{}</option>'.format(
                self.product.pk, self.product.name),
            html=True)

        for comp in (self.comp_application, self.comp_database, self.comp_cli, self.comp_api):
            comp_option = '<option value="{}">{}</option>'.format(comp.pk, comp.name)
            self.assertContains(response, comp_option, html=True)

    def test_add_components(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        post_data = {
            'product': self.product.pk,
            'o_component': [self.comp_application.pk, self.comp_database.pk],
            'case': [self.case_1.pk],
            'a': 'add',
            'from_plan': self.plan.pk,
        }
        response = self.client.post(self.cases_component_url, post_data)
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok', 'errors_list': []})

        for comp in (self.comp_application, self.comp_database):
            case_components = TestCaseComponent.objects.filter(
                case=self.case_1, component=comp)
            self.assertTrue(case_components.exists())

    def test_missing_delete_perm(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        post_data = {
            'o_component': [self.comp_cli.pk, self.comp_api.pk],
            'case': [self.case_1.pk],
            'a': 'remove',
        }
        response = self.client.post(self.cases_component_url, post_data)
        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 1, 'response': 'Permission denied - delete', 'errors_list': []})

    def test_remove_components(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        user_should_have_perm(self.tester, 'testcases.delete_testcasecomponent')

        post_data = {
            'o_component': [self.comp_cli.pk, self.comp_api.pk],
            'case': [self.case_1.pk],
            'a': 'remove',
        }
        response = self.client.post(self.cases_component_url, post_data)

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok', 'errors_list': []})

        for comp in (self.comp_cli, self.comp_api):
            case_components = TestCaseComponent.objects.filter(
                case=self.case_1, component=comp)
            self.assertFalse(case_components.exists())


class TestOperateCategoryView(BasePlanCase):
    """Tests for operating category on cases"""

    @classmethod
    def setUpTestData(cls):
        super(TestOperateCategoryView, cls).setUpTestData()

        cls.case_cat_full_auto = CategoryFactory(name='Full Auto', product=cls.product)
        cls.case_cat_full_manual = CategoryFactory(name='Full Manual', product=cls.product)

        user_should_have_perm(cls.tester, 'testcases.add_testcasecomponent')

        cls.case_category_url = reverse('testcases-category')

    def test_show_categories_form(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

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
            """<select multiple="multiple" id="id_o_category" name="o_category">
{}
</select>""".format(''.join(categories)),
            html=True)

    def test_update_cases_category(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username,
            password='password')

        post_data = {
            'from_plan': self.plan.pk,
            'product': self.product.pk,
            'case': [self.case_1.pk, self.case_3.pk],
            'a': 'update',
            'o_category': self.case_cat_full_auto.pk,
        }
        response = self.client.post(self.case_category_url, post_data)

        self.assertJSONEqual(
            str(response.content, encoding=settings.DEFAULT_CHARSET),
            {'rc': 0, 'response': 'ok', 'errors_list': []})

        for pk in (self.case_1.pk, self.case_3.pk):
            case = TestCase.objects.get(pk=pk)
            self.assertEqual(self.case_cat_full_auto, case.category)


class TestAddIssueToCase(BasePlanCase):
    """Tests for adding issue to case"""

    @classmethod
    def setUpTestData(cls):
        super(TestAddIssueToCase, cls).setUpTestData()

        cls.plan_tester = User.objects.create_user(  # nosec:B106:hardcoded_password_funcarg
            username='plantester',
            email='plantester@example.com',
            password='password')
        user_should_have_perm(cls.plan_tester, 'testcases.change_bug')

        cls.case_bug_url = reverse('testcases-bug', args=[cls.case_1.pk])
        cls.issue_tracker = BugSystem.objects.get(name='Bugzilla')

    def test_add_and_remove_a_bug(self):
        user_should_have_perm(self.plan_tester, 'testcases.add_bug')
        user_should_have_perm(self.plan_tester, 'testcases.delete_bug')

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
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

        cls.plan_tester = User.objects.create_user(  # nosec:B106:hardcoded_password_funcarg
            username='plantester',
            email='plantester@example.com',
            password='password')

        cls.case_plans_url = reverse('testcases-plan', args=[cls.case_1.pk])

    def tearDown(self):
        remove_perm_from_user(self.plan_tester, 'testcases.add_testcaseplan')
        remove_perm_from_user(self.plan_tester, 'testcases.change_testcaseplan')

    def assert_list_case_plans(self, response, case):
        for case_plan_rel in TestCasePlan.objects.filter(case=case):
            plan = case_plan_rel.plan
            self.assertContains(
                response,
                '<a href="{0}">{1}</a>'.format(plan.get_full_url(), plan.pk),
                html=True)

            self.assertContains(
                response,
                '<a href="{}">{}</a>'.format(plan.get_full_url(), plan.name),
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
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        response = self.client.get(self.case_plans_url,
                                   {'a': 'add', 'plan_id': self.plan_test_add.pk})

        self.assert_list_case_plans(response, self.case_1)

        self.assertTrue(TestCasePlan.objects.filter(
            plan=self.plan_test_add, case=self.case_1).exists())

    def test_remove_a_plan(self):
        user_should_have_perm(self.plan_tester, 'testcases.change_testcaseplan')
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        response = self.client.get(self.case_plans_url,
                                   {'a': 'remove', 'plan_id': self.plan_test_remove.pk})

        self.assert_list_case_plans(response, self.case_1)

        not_linked_to_plan = not TestCasePlan.objects.filter(
            case=self.case_1, plan=self.plan_test_remove).exists()
        self.assertTrue(not_linked_to_plan)

    def test_add_a_few_plans(self):
        user_should_have_perm(self.plan_tester, 'testcases.add_testcaseplan')
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username,
            password='password')
        # This time, add a few plans to another case
        url = reverse('testcases-plan', args=[self.case_2.pk])

        response = self.client.get(url,
                                   {'a': 'add', 'plan_id': [self.plan_test_add.pk,
                                                            self.plan_test_remove.pk]})

        self.assert_list_case_plans(response, self.case_2)

        self.assertTrue(TestCasePlan.objects.filter(
            case=self.case_2, plan=self.plan_test_add).exists())
        self.assertTrue(TestCasePlan.objects.filter(
            case=self.case_2, plan=self.plan_test_remove).exists())


class TestEditCase(BasePlanCase):
    """Test edit view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestEditCase, cls).setUpTestData()

        cls.proposed_case = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_proposed,
            plan=[cls.plan])

        user_should_have_perm(cls.tester, 'testcases.change_testcase')
        cls.case_edit_url = reverse('testcases-edit', args=[cls.case_1.pk])

        # Copy, then modify or add new data for specific tests below
        cls.edit_data = {
            'from_plan': cls.plan.pk,
            'summary': cls.case_1.summary,
            'product': cls.case_1.category.product.pk,
            'category': cls.case_1.category.pk,
            'default_tester': '',
            'estimated_time': '0',
            'case_status': cls.case_status_confirmed.pk,
            'arguments': '',
            'extra_link': '',
            'notes': '',
            'is_automated': '0',
            'requirement': '',
            'script': '',
            'alias': '',
            'priority': cls.case_1.priority.pk,
            'tag': 'RHEL',
            'setup': '',
            'action': '',
            'breakdown': '',
            'effect': '',
            'cc_list': '',
        }

    def test_404_if_case_id_not_exist(self):
        url = reverse('testcases-edit', args=[99999])
        response = self.client.get(url)
        self.assert404(response)

    def test_404_if_from_plan_not_exist(self):
        response = self.client.get(self.case_edit_url, {'from_plan': 9999})
        self.assert404(response)

    def test_show_edit_page(self):
        response = self.client.get(self.case_edit_url)
        self.assertEqual(200, response.status_code)

    def test_edit_a_case(self):
        edit_data = self.edit_data.copy()
        new_summary = 'Edited: {0}'.format(self.case_1.summary)
        edit_data['summary'] = new_summary

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = '{0}?from_plan={1}'.format(
            reverse('testcases-get', args=[self.case_1.pk]),
            self.plan.pk,
        )
        self.assertRedirects(response, redirect_url)

        edited_case = TestCase.objects.get(pk=self.case_1.pk)
        self.assertEqual(new_summary, edited_case.summary)

    def test_continue_edit_this_case_after_save(self):
        edit_data = self.edit_data.copy()
        edit_data['_continue'] = 'continue edit'

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = '{0}?from_plan={1}'.format(
            reverse('testcases-edit', args=[self.case_1.pk]),
            self.plan.pk,
        )
        self.assertRedirects(response, redirect_url)

    def test_continue_edit_next_confirmed_case_after_save(self):
        edit_data = self.edit_data.copy()
        edit_data['_continuenext'] = 'continue edit next case'

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = '{0}?from_plan={1}'.format(
            reverse('testcases-edit', args=[self.case_2.pk]),
            self.plan.pk,
        )
        self.assertRedirects(response, redirect_url)

    def test_continue_edit_next_non_confirmed_case_after_save(self):
        edit_data = self.edit_data.copy()
        edit_data['case_status'] = self.case_status_proposed.pk
        edit_data['_continuenext'] = 'continue edit next case'

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = '{0}?from_plan={1}'.format(
            reverse('testcases-edit', args=[self.proposed_case.pk]),
            self.plan.pk,
        )
        self.assertRedirects(response, redirect_url)

    def test_return_to_plan_confirmed_cases_tab(self):
        edit_data = self.edit_data.copy()
        edit_data['_returntoplan'] = 'return to plan'

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = '{0}#testcases'.format(
            reverse('test_plan_url_short', args=[self.plan.pk])
        )
        self.assertRedirects(response, redirect_url, target_status_code=301)

    def test_return_to_plan_review_cases_tab(self):
        edit_data = self.edit_data.copy()
        edit_data['case_status'] = self.case_status_proposed.pk
        edit_data['_returntoplan'] = 'return to plan'

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = '{0}#reviewcases'.format(
            reverse('test_plan_url_short', args=[self.plan.pk])
        )
        self.assertRedirects(response, redirect_url, target_status_code=301)


class TestAJAXSearchCases(BasePlanCase):
    """Test ajax_search"""

    @classmethod
    def setUpTestData(cls):
        super(TestAJAXSearchCases, cls).setUpTestData()

        # test data for Issue #78
        # https://github.com/kiwitcms/Kiwi/issues/78
        cls.case_bogus_summary = TestCaseFactory(
            summary=r"""A Test Case with backslash(\), single quotes(') and double quotes(")""",
            plan=[cls.plan])

        cls.search_data = {
            'summary': '',
            'author': '',
            'product': '',
            'plan': '',
            'is_automated': '',
            'category': '',
            'component': '',
            'bug_id': '',
            'tag__name__in': '',
            'a': 'search',
        }

        cls.search_url = reverse('testcases-ajax_search')

    def test_search_all_cases(self):
        response = self.client.get(self.search_url, self.search_data)
        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        cases_count = self.plan.case.count()
        self.assertEqual(cases_count, data['iTotalRecords'])
        self.assertEqual(cases_count, data['iTotalDisplayRecords'])


class TestChangeCasesAutomated(BasePlanCase):
    """Test automated view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestChangeCasesAutomated, cls).setUpTestData()

        cls.change_data = {
            'case': [cls.case_1.pk, cls.case_2.pk],
            'a': 'change',
            # Add necessary automated value here:
            # o_is_automated
            # o_is_manual
            # o_is_automated_proposed
        }

        user_should_have_perm(cls.tester, 'testcases.change_testcase')
        cls.change_url = reverse('testcases-automated')

    def test_update_automated(self):
        change_data = self.change_data.copy()
        change_data['o_is_automated'] = 'on'

        response = self.client.post(self.change_url, change_data)

        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})

        for pk in self.change_data['case']:
            case = TestCase.objects.get(pk=pk)
            self.assertEqual(1, case.is_automated)

    def test_update_manual(self):
        change_data = self.change_data.copy()
        change_data['o_is_manual'] = 'on'

        response = self.client.post(self.change_url, change_data)

        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})

        for pk in self.change_data['case']:
            case = TestCase.objects.get(pk=pk)
            self.assertEqual(0, case.is_automated)

    def test_update_automated_proposed(self):
        change_data = self.change_data.copy()
        change_data['o_is_automated_proposed'] = 'on'

        response = self.client.post(self.change_url, change_data)

        self.assertJsonResponse(response, {'rc': 0, 'response': 'ok'})

        for pk in self.change_data['case']:
            case = TestCase.objects.get(pk=pk)
            self.assertTrue(case.is_automated_proposed)


class TestExportCases(BasePlanCase):
    """Test export view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestExportCases, cls).setUpTestData()
        cls.export_url = reverse('testcases-export')

    def test_export_cases(self):
        response = self.client.post(self.export_url,
                                    {'case': [self.case_1.pk, self.case_2.pk]})

        today = datetime.now()
        # Verify header
        self.assertEqual(
            'attachment; filename=tcms-testcases-%02i-%02i-%02i.xml' % (
                today.year, today.month, today.day),
            response['Content-Disposition'])
        # verify content

        xmldoc = xml.etree.ElementTree.fromstring(response.content)  # nosec:B314:blacklist
        exported_cases_count = xmldoc.findall('testcase')
        self.assertEqual(2, len(exported_cases_count))


class TestPrintablePage(BasePlanCase):
    """Test printable page view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestPrintablePage, cls).setUpTestData()
        cls.printable_url = reverse('testcases-printable')

        cls.case_1.add_text(action='action',
                            effect='effect',
                            setup='setup',
                            breakdown='breakdown')
        cls.case_2.add_text(action='action',
                            effect='effect',
                            setup='setup',
                            breakdown='breakdown')

    def test_printable_page(self):
        # printing only 1 of the cases
        response = self.client.post(self.printable_url,
                                    {'case': [self.case_1.pk]})

        # not printing the Test Plan header section
        self.assertNotContains(response, 'Test Plan Document')

        # response contains the first TestCase
        self.assertContains(
            response,
            '<h3>[{0}] {1}</h3>'.format(self.case_1.pk, self.case_1.summary),
            html=True
        )

        # but not the second TestCase b/c it was not selected
        self.assertNotContains(
            response,
            '<h3>[{0}] {1}</h3>'.format(self.case_2.pk, self.case_2.summary),
            html=True
        )


class TestCloneCase(BasePlanCase):
    """Test clone view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestCloneCase, cls).setUpTestData()

        user_should_have_perm(cls.tester, 'testcases.add_testcase')
        cls.clone_url = reverse('testcases-clone')

    def test_refuse_if_missing_argument(self):
        # Refuse to clone cases if missing selectAll and case arguments
        response = self.client.get(self.clone_url, {}, follow=True)

        self.assertContains(response, 'At least one TestCase is required')

    def test_show_clone_page_with_from_plan(self):
        response = self.client.get(self.clone_url,
                                   {'from_plan': self.plan.pk,
                                    'case': [self.case_1.pk, self.case_2.pk]})

        self.assertContains(
            response,
            """<div>
    <input type="radio" id="id_use_sameplan" name="selectplan" value="{0}">
    <label for="id_use_sameplan" class="strong">Use the same Plan -- {0} : {1}</label>
</div>""".format(self.plan.pk, self.plan.name),
            html=True)

        for loop_counter, case in enumerate([self.case_1, self.case_2]):
            self.assertContains(
                response,
                '<label for="id_case_{0}">'
                '<input checked="checked" id="id_case_{0}" name="case" '
                'type="checkbox" value="{1}"> {2}</label>'.format(
                    loop_counter, case.pk, case.summary),
                html=True)

    def test_show_clone_page_without_from_plan(self):
        response = self.client.get(self.clone_url, {'case': self.case_1.pk})

        self.assertNotContains(
            response,
            'Use the same Plan -- {0} : {1}'.format(self.plan.pk,
                                                    self.plan.name),
        )

        self.assertContains(
            response,
            '<label for="id_case_0">'
            '<input checked="checked" id="id_case_0" name="case" '
            'type="checkbox" value="{0}"> {1}</label>'.format(
                self.case_1.pk, self.case_1.summary),
            html=True)


class TestSearchCases(BasePlanCase):
    """Test search view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestSearchCases, cls).setUpTestData()

        cls.search_url = reverse('testcases-search')

    def test_search_without_selected_product(self):
        response = self.client.get(self.search_url, {})
        self.assertContains(
            response,
            '<option value="" selected="selected">---------</option>',
            html=True)

    def test_search_with_selected_product(self):
        response = self.client.get(self.search_url,
                                   {'product': self.product.pk})
        self.assertContains(
            response,
            '<option value="{0}" selected="selected">{1}</option>'.format(
                self.product.pk, self.product.name),
            html=True
        )


class TestAJAXResponse(BasePlanCase):
    """Test ajax_response"""

    def setUp(self):
        self.factory = RequestFactory()

        self.column_names = [
            'case_id',
            'summary',
            'author__username',
            'default_tester__username',
            'is_automated',
            'case_status__name',
            'category__name',
            'priority__value',
            'create_date',
        ]

        self.template = 'case/common/json_cases.txt'

    def test_return_empty_cases(self):
        url = reverse('testcases-ajax_search')
        request = self.factory.get(url, {

        })
        request.user = self.tester

        empty_cases = TestCase.objects.none()
        response = ajax_response(request, empty_cases, self.column_names, self.template)

        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        self.assertEqual(0, data['sEcho'])
        self.assertEqual(0, data['iTotalRecords'])
        self.assertEqual(0, data['iTotalDisplayRecords'])
        self.assertEqual([], data['aaData'])

    def test_return_sorted_cases_by_name_desc(self):
        url = reverse('testcases-ajax_search')
        request = self.factory.get(url, {
            'sEcho': 1,
            'iDisplayStart': 0,
            'iDisplayLength': 2,
            'iSortCol_0': 0,
            'sSortDir_0': 'desc',
            'iSortingCols': 1,
            'bSortable_0': 'true',
            'bSortable_1': 'true',
            'bSortable_2': 'true',
            'bSortable_3': 'true',
        })
        request.user = self.tester

        cases = self.plan.case.all()
        response = ajax_response(request, cases, self.column_names, self.template)

        data = json.loads(str(response.content, encoding=settings.DEFAULT_CHARSET))

        total = self.plan.case.count()
        self.assertEqual(1, data['sEcho'])
        self.assertEqual(total, data['iTotalRecords'])
        self.assertEqual(total, data['iTotalDisplayRecords'])
        self.assertEqual(2, len(data['aaData']))

        id_links = [row[2] for row in data['aaData']]
        id_links.sort()
        expected_id_links = [
            "<a href='{0}'>{1}</a>".format(
                reverse('testcases-get', args=[case.pk]),
                case.pk,
            )
            for case in self.plan.case.order_by('-pk')[0:2]
        ]
        expected_id_links.sort()
        self.assertEqual(expected_id_links, id_links)


class TestGetCasesFromPlan(BasePlanCase):
    def test_casetags_are_shown_in_template(self):
        tag, _ = Tag.objects.get_or_create(name='Linux')
        self.case.add_tag(tag)

        url = reverse('testcases-all')
        response_data = urlencode({
            'from_plan': self.plan.pk,
            'template_type': 'case',
            'a': 'initial'})
        # note: this is how the UI sends the request
        response = self.client.post(url, data=response_data,
                                    content_type='application/x-www-form-urlencoded; charset=UTF-8',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, 'Tags:')
        self.assertContains(response, '<a href="#testcases">Linux</a>')
