# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

import unittest
from http import HTTPStatus
from urllib.parse import urlencode

from django.urls import reverse
from django.forms import ValidationError
from django.test import RequestFactory

from tcms.testcases.fields import MultipleEmailField
from tcms.management.models import Priority, Tag
from tcms.testcases.models import TestCase
from tcms.testcases.views import get_selected_testcases
from tcms.testruns.models import TestCaseRunStatus
from tcms.tests.factories import BugFactory
from tcms.tests.factories import TestCaseFactory
from tcms.tests import BasePlanCase, BaseCaseRun
from tcms.tests import user_should_have_perm
from tcms.utils.permissions import initiate_user_with_default_setups


class TestGetCaseRunDetailsAsDefaultUser(BaseCaseRun):
    """Assert what a default user (non-admin) will see"""

    def test_user_in_default_group_sees_comments(self):
        # test for https://github.com/kiwitcms/Kiwi/issues/74
        initiate_user_with_default_setups(self.tester)

        url = reverse('caserun-detail-pane', args=[self.case_run_1.case_id])
        response = self.client.get(
            url,
            {
                'case_run_id': self.case_run_1.pk,
                'case_text_version': self.case_run_1.case.history.latest().history_id,
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

    def test_user_sees_bugs(self):
        bug_1 = BugFactory()
        bug_2 = BugFactory()

        self.case_run_1.add_bug(bug_1.bug_id, bug_1.bug_system.pk)
        self.case_run_1.add_bug(bug_2.bug_id, bug_2.bug_system.pk)

        url = reverse('caserun-detail-pane', args=[self.case_run_1.case.pk])
        response = self.client.get(
            url,
            {
                'case_run_id': self.case_run_1.pk,
                'case_text_version': self.case_run_1.case.history.latest().history_id,
            }
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertContains(response, bug_1.get_full_url())
        self.assertContains(response, bug_2.get_full_url())


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

        # test data for https://github.com/kiwitcms/Kiwi/issues/334
        # pylint: disable=objects-update-used
        Priority.objects.filter(value='P4').update(is_active=False)

        user_should_have_perm(cls.tester, 'testcases.change_testcase')
        cls.case_edit_url = reverse('testcases-edit', args=[cls.case_1.pk])

        # Copy, then modify or add new data for specific tests below
        cls.edit_data = {
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
        self.assertNotContains(response, ">P4</option")

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


class TestPrintablePage(BasePlanCase):
    """Test printable page view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.printable_url = reverse('testcases-printable')

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
        super().setUpTestData()

        cls.search_url = reverse('testcases-search')

    def test_page_renders(self):
        response = self.client.get(self.search_url, {})
        self.assertContains(response, '<option value="">----------</option>', html=True)


class TestGetCasesFromPlan(BasePlanCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def test_casetags_are_shown_in_template(self):
        # pylint: disable=tag-objects-get_or_create
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
