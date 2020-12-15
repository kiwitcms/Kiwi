# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors
# pylint: disable=objects-update-used

import unittest
from http import HTTPStatus

from django.forms import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.management.models import Priority
from tcms.testcases.fields import MultipleEmailField
from tcms.testcases.models import TestCase, TestCasePlan, TestCaseStatus
from tcms.tests import (
    BaseCaseRun,
    BasePlanCase,
    PermissionsTestCase,
    remove_perm_from_user,
    user_should_have_perm,
)
from tcms.tests.factories import TestCaseFactory


class TestGetTestCase(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, "testcases.view_testcase")

    def test_test_case_is_shown(self):
        url = reverse("testcases-get", args=[self.case_1.pk])
        response = self.client.get(url)

        # will not fail when running under different locale
        self.assertEqual(HTTPStatus.OK, response.status_code)


class TestMultipleEmailField(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.field = MultipleEmailField()

    def test_to_python(self):
        value = u"zhangsan@localhost"
        pyobj = self.field.to_python(value)
        self.assertEqual(pyobj, [value])

        value = u"zhangsan@localhost,,lisi@example.com,"
        pyobj = self.field.to_python(value)
        self.assertEqual(pyobj, [u"zhangsan@localhost", u"lisi@example.com"])

        for value in ("", None, []):
            pyobj = self.field.to_python(value)
            self.assertEqual(pyobj, [])

    def test_clean(self):
        value = "zhangsan@localhost"
        data = self.field.clean(value)
        self.assertEqual(data, value)

        data = self.field.clean("zhangsan@localhost,lisi@example.com")
        self.assertEqual(data, "zhangsan@localhost,lisi@example.com")

        data = self.field.clean(",zhangsan@localhost, ,lisi@example.com, \n")
        self.assertEqual(data, "zhangsan@localhost,lisi@example.com")

        with self.assertRaises(ValidationError):
            self.field.clean(",zhangsan,zhangsan@localhost, \n,lisi@example.com, ")

        with self.assertRaises(ValidationError):
            self.field.required = True
            self.field.clean("")

        self.field.required = False
        data = self.field.clean("")
        self.assertEqual(data, "")


class TestNewCase(BasePlanCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.new_case_url = reverse("testcases-new")

        cls.summary = "summary"
        cls.text = "some text description"
        cls.script = "some script"
        cls.arguments = "args1, args2, args3"
        cls.requirement = "requirement"
        cls.link = "http://somelink.net"
        cls.notes = "notes"
        cls.data = {
            "author": cls.tester.pk,
            "summary": cls.summary,
            "default_tester": cls.tester.pk,
            "product": cls.case.category.product.pk,
            "category": cls.case.category.pk,
            "case_status": cls.case_status_confirmed.pk,
            "priority": cls.case.priority.pk,
            "text": cls.text,
            "script": cls.script,
            "arguments": cls.arguments,
            "requirement": cls.requirement,
            "extra_link": cls.link,
            "notes": cls.notes,
            "email_settings-0-auto_to_case_author": "on",
            "email_settings-0-auto_to_run_manager": "on",
            "email_settings-0-auto_to_case_run_assignee": "on",
            "email_settings-0-auto_to_case_tester": "on",
            "email_settings-0-auto_to_run_tester": "on",
            "email_settings-0-notify_on_case_update": "on",
            "email_settings-0-notify_on_case_delete": "on",
            "email_settings-0-cc_list": "info@example.com",
            "email_settings-0-case": "",
            "email_settings-0-id": cls.case.emailing.pk,
            "email_settings-TOTAL_FORMS": "1",
            "email_settings-INITIAL_FORMS": "1",
            "email_settings-MIN_NUM_FORMS": "0",
            "email_settings-MAX_NUM_FORMS": "1",
        }

        user_should_have_perm(cls.tester, "testcases.add_testcase")
        user_should_have_perm(cls.tester, "testcases.view_testcase")

    def test_notify_formset_invalid(self):
        # Note: Boolean fields are always valid - either False or True
        # That's why the only way to make the notify formset invalid is to
        # reference a non-existing email_settings ID !!!
        data = self.data.copy()
        data["email_settings-0-id"] = -1
        del data["email_settings-0-auto_to_case_tester"]

        response = self.client.post(self.new_case_url, data)

        self.assertContains(response, _("New TestCase"))
        self.assertContains(
            response,
            '<input class="bootstrap-switch" name="email_settings-0-auto_to_case_tester" '
            'type="checkbox"',
            html=False,
        )

    def test_create_test_case_successfully(self):
        response = self.client.post(self.new_case_url, self.data)

        test_case = TestCase.objects.get(summary=self.summary)
        redirect_url = reverse("testcases-get", args=[test_case.pk])

        self.assertRedirects(response, redirect_url)
        self._assertTestCase(test_case)

    def test_create_test_case_successfully_from_plan(self):
        self.data["from_plan"] = self.plan.pk

        response = self.client.post(self.new_case_url, self.data)

        test_case = TestCase.objects.get(summary=self.summary)
        redirect_url = reverse("testcases-get", args=[test_case.pk])

        self.assertRedirects(response, redirect_url)
        self.assertEqual(test_case.plan.get(), self.plan)
        self.assertEqual(
            TestCasePlan.objects.filter(case=test_case, plan=self.plan).count(), 1
        )
        self._assertTestCase(test_case)

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


class TestNewCasePermission(PermissionsTestCase):
    permission_label = "testcases.add_testcase"
    http_method_names = ["get", "post"]
    url = reverse("testcases-new")

    @classmethod
    def setUpTestData(cls):
        cls.summary = "summary"
        cls.post_data = {
            "summary": cls.summary,
        }
        super().setUpTestData()
        user_should_have_perm(cls.tester, "testcases.view_testcase")

        case_status_confirmed = TestCaseStatus.objects.filter(is_confirmed=True).first()

        case = TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=case_status_confirmed,
        )
        case.save()  # creates a new case entry in the database

        cls.post_data.update(
            {
                "author": cls.tester.pk,
                "default_tester": cls.tester.pk,
                "priority": case.priority.pk,
                "product": case.category.product.pk,
                "category": case.category.pk,
                "case_status": case_status_confirmed.pk,
                "text": "some text description",
                "script": "some script",
                "arguments": "args1, args2, args3",
                "email_settings-0-auto_to_case_author": "on",
                "email_settings-0-auto_to_run_manager": "on",
                "email_settings-0-auto_to_case_run_assignee": "on",
                "email_settings-0-auto_to_case_tester": "on",
                "email_settings-0-auto_to_run_tester": "on",
                "email_settings-0-notify_on_case_update": "on",
                "email_settings-0-notify_on_case_delete ": "on",
                "email_settings-0-cc_list": "info@example.com",
                "email_settings-0-case": "",
                "email_settings-0-id": case.emailing.pk,
                "email_settings-TOTAL_FORMS": "1",
                "email_settings-INITIAL_FORMS": "1",
                "email_settings-MIN_NUM_FORMS": "0",
                "email_settings-MAX_NUM_FORMS": "1",
            }
        )

    def verify_get_with_permission(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, _("New TestCase"))

    def verify_post_with_permission(self):
        response = self.client.post(self.url, self.post_data, follow=True)
        test_case = TestCase.objects.get(summary=self.summary)
        redirect_url = reverse("testcases-get", args=[test_case.pk])

        self.assertRedirects(
            response, redirect_url, status_code=302, target_status_code=200
        )
        self.assertContains(response, self.summary)


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
            plan=[cls.plan],
        )

        # test data for https://github.com/kiwitcms/Kiwi/issues/334

        Priority.objects.filter(value="P4").update(is_active=False)

        user_should_have_perm(cls.tester, "testcases.change_testcase")
        user_should_have_perm(cls.tester, "testcases.view_testcase")
        cls.case_edit_url = reverse("testcases-edit", args=[cls.case_1.pk])

        # Copy, then modify or add new data for specific tests below
        cls.edit_data = {
            "author": cls.case_1.author.pk,
            "from_plan": cls.plan.pk,
            "summary": cls.case_1.summary,
            "product": cls.case_1.category.product.pk,
            "category": cls.case_1.category.pk,
            "default_tester": "",
            "case_status": cls.case_status_confirmed.pk,
            "arguments": "",
            "extra_link": "",
            "notes": "",
            "is_automated": "0",
            "requirement": "",
            "script": "",
            "priority": cls.case_1.priority.pk,
            "tag": "RHEL",
            "text": "Given-When-Then",
            "email_settings-0-auto_to_case_author": "on",
            "email_settings-0-auto_to_run_manager": "on",
            "email_settings-0-auto_to_case_run_assignee": "on",
            "email_settings-0-auto_to_case_tester": "on",
            "email_settings-0-auto_to_run_tester": "on",
            "email_settings-0-notify_on_case_update": "on",
            "email_settings-0-notify_on_case_delete": "on",
            "email_settings-0-cc_list": "",
            "email_settings-0-case": cls.case_1.pk,
            "email_settings-0-id": cls.case_1.emailing.pk,
            "email_settings-TOTAL_FORMS": "1",
            "email_settings-INITIAL_FORMS": "1",
            "email_settings-MIN_NUM_FORMS": "0",
            "email_settings-MAX_NUM_FORMS": "1",
        }

    def test_404_if_case_id_not_exist(self):
        url = reverse("testcases-edit", args=[99999])
        response = self.client.get(url)
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_show_edit_page(self):
        response = self.client.get(self.case_edit_url)
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, ">P4</option")

    def test_edit_a_case(self):
        edit_data = self.edit_data.copy()
        new_summary = "Edited: {0}".format(self.case_1.summary)
        edit_data["summary"] = new_summary

        response = self.client.post(self.case_edit_url, edit_data)

        redirect_url = reverse("testcases-get", args=[self.case_1.pk])
        self.assertRedirects(response, redirect_url)

        self.case_1.refresh_from_db()
        self.assertEqual(new_summary, self.case_1.summary)


class TestCloneCase(BasePlanCase):
    """Test clone view method"""

    @classmethod
    def setUpTestData(cls):
        super(TestCloneCase, cls).setUpTestData()

        user_should_have_perm(cls.tester, "testcases.add_testcase")
        cls.clone_url = reverse("testcases-clone")

    def test_refuse_if_missing_argument(self):
        # Refuse to clone cases if missing selectAll and case arguments
        response = self.client.get(self.clone_url, {}, follow=True)

        self.assertContains(response, _("At least one TestCase is required"))

    def test_show_clone_page_with_selected_cases(self):
        response = self.client.get(
            self.clone_url, {"case": [self.case_1.pk, self.case_2.pk]}
        )

        self.assertContains(response, "TP-%s: %s" % (self.plan.pk, self.plan.name))

        for case in [self.case_1, self.case_2]:
            self.assertContains(response, "TC-%d: %s" % (case.pk, case.summary))

    def test_user_without_permission_should_not_be_able_to_clone_a_case(self):
        remove_perm_from_user(self.tester, "testcases.add_testcase")
        base_url = reverse("tcms-login") + "?next="
        expected = base_url + reverse("testcases-clone") + "?case=%d" % self.case_1.pk
        response = self.client.get(
            self.clone_url,
            {
                "case": [
                    self.case_1.pk,
                ]
            },
        )

        self.assertRedirects(response, expected)


class TestSearchCases(BasePlanCase):
    """Test search view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.search_url = reverse("testcases-search")
        user_should_have_perm(cls.tester, "testcases.view_testcase")

    def test_page_renders(self):
        response = self.client.get(self.search_url, {})
        self.assertContains(response, '<option value="">----------</option>', html=True)

    def test_get_parameter_should_be_accepted_for_a_product(self):
        response = self.client.get(self.search_url, {"product": self.product.pk})
        self.assertContains(
            response,
            '<option value="%d" selected>%s</option>'
            % (self.product.pk, self.product.name),
            html=True,
        )
