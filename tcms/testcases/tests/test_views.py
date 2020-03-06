# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

import unittest
from http import HTTPStatus
from urllib.parse import urlencode

from django.forms import ValidationError
from django.test import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.management.models import Priority, Tag
from tcms.testcases.fields import MultipleEmailField
from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testcases.views import get_selected_testcases
from tcms.tests import (BaseCaseRun, BasePlanCase, remove_perm_from_user,
                        user_should_have_perm)
from tcms.tests.factories import TestCaseFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestGetTestCase(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, 'testcases.view_testcase')

    def test_test_case_is_shown(self):
        url = reverse('testcases-get', args=[self.case_1.pk])
        response = self.client.get(url)

        # will not fail when running under different locale
        self.assertEqual(HTTPStatus.OK, response.status_code)


class TestMultipleEmailField(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.field = MultipleEmailField()

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
        value = 'zhangsan@localhost'
        data = self.field.clean(value)
        self.assertEqual(data, value)

        data = self.field.clean('zhangsan@localhost,lisi@example.com')
        self.assertEqual(data, 'zhangsan@localhost,lisi@example.com')

        data = self.field.clean(',zhangsan@localhost, ,lisi@example.com, \n')
        self.assertEqual(data, 'zhangsan@localhost,lisi@example.com')

        with self.assertRaises(ValidationError):
            self.field.clean(',zhangsan,zhangsan@localhost, \n,lisi@example.com, ')

        with self.assertRaises(ValidationError):
            self.field.required = True
            self.field.clean('')

        self.field.required = False
        data = self.field.clean('')
        self.assertEqual(data, '')


class TestNewCase(BasePlanCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.new_case_url = reverse('testcases-new')

        cls.summary = 'summary'
        cls.text = 'some text description'
        cls.script = 'some script'
        cls.arguments = 'args1, args2, args3'
        cls.requirement = 'requirement'
        cls.link = 'http://somelink.net'
        cls.notes = 'notes'
        cls.data = {
            'author': cls.tester.pk,
            'summary': cls.summary,
            'default_tester': cls.tester.pk,
            'product': cls.case.category.product.pk,
            'category': cls.case.category.pk,
            'case_status': cls.case_status_confirmed.pk,
            'priority': cls.case.priority.pk,
            'text': cls.text,
            'script': cls.script,
            'arguments': cls.arguments,
            'requirement': cls.requirement,
            'extra_link': cls.link,
            'notes': cls.notes,

            'email_settings-0-auto_to_case_author': 'on',
            'email_settings-0-auto_to_run_manager': 'on',
            'email_settings-0-auto_to_case_run_assignee': 'on',
            'email_settings-0-auto_to_case_tester': 'on',
            'email_settings-0-auto_to_run_tester': 'on',
            'email_settings-0-notify_on_case_update': 'on',
            'email_settings-0-notify_on_case_delete': 'on',
            'email_settings-0-cc_list': 'info@example.com',
            'email_settings-0-case': '',
            'email_settings-0-id': cls.case.emailing.pk,
            'email_settings-TOTAL_FORMS': '1',
            'email_settings-INITIAL_FORMS': '1',
            'email_settings-MIN_NUM_FORMS': '0',
            'email_settings-MAX_NUM_FORMS': '1',
        }

        user_should_have_perm(cls.tester, 'testcases.add_testcase')
        user_should_have_perm(cls.tester, 'testcases.view_testcase')

    def test_create_test_case_successfully(self):
        response = self.client.post(self.new_case_url, self.data)

        test_case = TestCase.objects.get(summary=self.summary)
        redirect_url = reverse('testcases-get', args=[test_case.pk])

        self.assertRedirects(response, redirect_url)
        self._assertTestCase(test_case)

    def test_create_test_case_successfully_from_plan(self):
        self.data['from_plan'] = self.plan.pk

        response = self.client.post(self.new_case_url, self.data)

        test_case = TestCase.objects.get(summary=self.summary)
        redirect_url = reverse('testcases-get', args=[test_case.pk])

        self.assertRedirects(response, redirect_url)
        self.assertEqual(test_case.plan.get(), self.plan)
        self.assertEqual(TestCasePlan.objects.filter(case=test_case, plan=self.plan).count(), 1)
        self._assertTestCase(test_case)

    def test_create_test_case_without_permissions(self):
        remove_perm_from_user(self.tester, 'testcases.add_testcase')

        response = self.client.post(self.new_case_url, self.data)
        redirect_url = "{0}?next={1}".format(
            reverse('tcms-login'), reverse('testcases-new')
        )

        self.assertRedirects(response, redirect_url)
        # assert test case has not been created
        self.assertEqual(TestCase.objects.filter(summary=self.summary).count(), 0)

    def _assertTestCase(self, test_case):
        self.assertEqual(test_case.author, self.tester)
        self.assertEqual(test_case.summary, self.summary)
        self.assertEqual(test_case.category, self.case.category)
        self.assertEqual(test_case.default_tester, self.tester)
        self.assertEqual(test_case.case_status, self.case_status_confirmed)
        self.assertEqual(test_case.priority, self.case.priority)
        self.assertEqual(test_case.text, self.text)
        self.assertEqual(test_case.script, self.script)
        self.assertEqual(test_case.arguments, self.arguments)
        self.assertEqual(test_case.requirement, self.requirement)
        self.assertEqual(test_case.extra_link, self.link)
        self.assertEqual(test_case.notes, self.notes)


class TestEditCase(BasePlanCase):
    """Test edit view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.proposed_case = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=cls.case_status_proposed,
            plan=[cls.plan])

        # test data for https://github.com/kiwitcms/Kiwi/issues/334
        # pylint: disable=objects-update-used
        Priority.objects.filter(value='P4').update(is_active=False)

        user_should_have_perm(cls.tester, 'testcases.change_testcase')
        user_should_have_perm(cls.tester, 'testcases.view_testcase')
        cls.case_edit_url = reverse('testcases-edit', args=[cls.case_1.pk])

        # Copy, then modify or add new data for specific tests below
        cls.edit_data = {
            'author': cls.case_1.author.pk,
            'from_plan': cls.plan.pk,
            'summary': cls.case_1.summary,
            'product': cls.case_1.category.product.pk,
            'category': cls.case_1.category.pk,
            'default_tester': '',
            'case_status': cls.case_status_confirmed.pk,
            'arguments': '',
            'extra_link': '',
            'notes': '',
            'is_automated': '0',
            'requirement': '',
            'script': '',
            'priority': cls.case_1.priority.pk,
            'tag': 'RHEL',
            'text': 'Given-When-Then',

            'email_settings-0-auto_to_case_author': 'on',
            'email_settings-0-auto_to_run_manager': 'on',
            'email_settings-0-auto_to_case_run_assignee': 'on',
            'email_settings-0-auto_to_case_tester': 'on',
            'email_settings-0-auto_to_run_tester': 'on',
            'email_settings-0-notify_on_case_update': 'on',
            'email_settings-0-notify_on_case_delete': 'on',
            'email_settings-0-cc_list': '',
            'email_settings-0-case': cls.case_1.pk,
            'email_settings-0-id': cls.case_1.emailing.pk,
            'email_settings-TOTAL_FORMS': '1',
            'email_settings-INITIAL_FORMS': '1',
            'email_settings-MIN_NUM_FORMS': '0',
            'email_settings-MAX_NUM_FORMS': '1',
        }

    def test_404_if_case_id_not_exist(self):
        url = reverse('testcases-edit', args=[99999])
        response = self.client.get(url)
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_show_edit_page(self):
        response = self.client.get(self.case_edit_url)
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, ">P4</option")

    def test_edit_a_case(self):
        edit_data = self.edit_data.copy()
        new_summary = 'Edited: {0}'.format(self.case_1.summary)
        edit_data['summary'] = new_summary

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = reverse('testcases-get', args=[self.case_1.pk])
        self.assertRedirects(response, redirect_url)

        self.case_1.refresh_from_db()
        self.assertEqual(new_summary, self.case_1.summary)


class TestPrintablePage(BasePlanCase):
    """Test printable page view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.printable_url = reverse('testcases-printable')
        user_should_have_perm(cls.tester, 'testcases.view_testcase')

    def test_printable_page(self):
        # printing only 1 of the cases
        response = self.client.post(self.printable_url,
                                    {'case': [self.case_1.pk]})

        # not printing the Test Plan header section
        self.assertNotContains(response, 'Test Plan Document')

        # response contains the first TestCase
        self.assertContains(
            response,
            '<h3>TC-{0}: {1}</h3>'.format(self.case_1.pk, self.case_1.summary),
            html=True
        )

        # but not the second TestCase b/c it was not selected
        self.assertNotContains(
            response,
            '<h3>TC-{0}: {1}'.format(self.case_2.pk, self.case_2.summary),
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

        self.assertContains(response, _('At least one TestCase is required'))

    def test_show_clone_page_with_selected_cases(self):
        response = self.client.get(self.clone_url,
                                   {'case': [self.case_1.pk, self.case_2.pk]})

        self.assertContains(response, "TP-%s: %s" % (self.plan.pk, self.plan.name))

        for case in [self.case_1, self.case_2]:
            self.assertContains(response,
                                "TC-%d: %s" % (case.pk, case.summary))

    def test_user_without_permission_should_not_be_able_to_clone_a_case(self):
        remove_perm_from_user(self.tester, 'testcases.add_testcase')
        base_url = reverse('tcms-login') + '?next='
        expected = base_url + reverse('testcases-clone') + "?case=%d" % self.case_1.pk
        response = self.client.get(self.clone_url, {'case': [self.case_1.pk, ]})

        self.assertRedirects(
            response,
            expected
        )


class TestSearchCases(BasePlanCase):
    """Test search view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.search_url = reverse('testcases-search')
        user_should_have_perm(cls.tester, 'testcases.view_testcase')

    def test_page_renders(self):
        response = self.client.get(self.search_url, {})
        self.assertContains(response, '<option value="">----------</option>', html=True)

    def test_get_parameter_should_be_accepted_for_a_product(self):
        response = self.client.get(self.search_url, {'product': self.product.pk})
        self.assertContains(response,
                            '<option value="%d" selected>%s</option>' % (self.product.pk,
                                                                         self.product.name),
                            html=True)


class TestGetCasesFromPlan(BasePlanCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def test_casetags_are_shown_in_template(self):
        tag, _created = Tag.get_or_create(self.tester, 'Linux')
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
        self.assertContains(response, _('Tags'))
        self.assertContains(response, '<a href="#testcases">Linux</a>')

    def test_disabled_priority_now_shown(self):
        # test data for https://github.com/kiwitcms/Kiwi/issues/334
        # pylint: disable=objects-update-used
        Priority.objects.filter(value='P4').update(is_active=False)

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
        self.assertContains(response, 'Set P3')
        self.assertNotContains(response, 'Set P4')


class TestGetSelectedTestcases(BasePlanCase):
    def test_get_selected_testcases_works_with_both_string_and_int_pks(self):
        """
        Assures that tcms.testcases.views.get_selected_testcases
        returns the same results, regardless of whether the
        passed request contains the case pks as strings or
        integers, as long as they are the same in both occasions.
        """

        case_int_pks = [self.case.pk, self.case_1.pk, self.case_2.pk, self.case_3.pk]
        case_str_pks = []

        for _pk in case_int_pks:
            case_str_pks.append(str(_pk))

        int_pk_query = get_selected_testcases(
            RequestFactory().post(
                reverse('testcases-clone'),
                {'case': case_int_pks}
            )
        )

        str_pk_query = get_selected_testcases(
            RequestFactory().post(
                reverse('testcases-clone'),
                {'case': case_str_pks}
            )
        )

        for case in TestCase.objects.filter(pk__in=case_int_pks):
            self.assertTrue(case in int_pk_query)
            self.assertTrue(case in str_pk_query)
