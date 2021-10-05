# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

from http import HTTPStatus

from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.testruns.models import TestExecutionStatus, TestRun
from tcms.tests import (
    BaseCaseRun,
    BasePlanCase,
    PermissionsTestCase,
    remove_perm_from_user,
    user_should_have_perm,
)
from tcms.tests.factories import (
    BuildFactory,
    TagFactory,
    TestExecutionFactory,
    TestRunFactory,
    UserFactory,
)
from tcms.utils.permissions import initiate_user_with_default_setups


class TestGetRun(BaseCaseRun):
    """Test get view method"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

        for _i in range(3):
            cls.test_run.add_tag(TagFactory())

        cls.unauthorized = UserFactory()
        cls.unauthorized.set_password("password")
        cls.unauthorized.save()

        cls.unauthorized.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(cls.unauthorized, "testruns.add_testruntag")
        remove_perm_from_user(cls.unauthorized, "testruns.delete_testruntag")

    def test_404_if_non_existing_pk(self):
        url = reverse("testruns-get", args=[99999999])
        response = self.client.get(url)
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)

    def test_get_a_run(self):
        url = reverse("testruns-get", args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        _tags = _("Tags")
        self.assertContains(
            response,
            f'<h2 class="card-pf-title"><span class="fa fa-tags"></span>{_tags}</h2>',
            html=True,
        )

    def test_get_run_without_permissions_to_add_or_remove_tags(self):
        self.client.logout()

        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.unauthorized.username, password="password"
        )

        url = reverse("testruns-get", args=[self.test_run.pk])
        response = self.client.get(url)

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertNotContains(response, "Add Tag")
        self.assertNotContains(response, "js-remove-tag")


class TestCreateNewRun(BasePlanCase):
    """Test creating new run"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.build = BuildFactory(version=cls.plan.product_version)

        user_should_have_perm(cls.tester, "testruns.add_testrun")
        user_should_have_perm(cls.tester, "testruns.view_testrun")
        cls.url = reverse("testruns-new")

    def test_get_shows_selected_cases(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.tester.username, password="password"
        )

        response = self.client.get(
            self.url,
            {"p": self.plan.pk, "c": [self.case_1.pk, self.case_2.pk, self.case_3.pk]},
        )

        # Assert listed cases
        for _i, case in enumerate((self.case_1, self.case_2, self.case_3), 1):
            case_url = reverse("testcases-get", args=[case.pk])
            self.assertContains(
                response,
                f'<a href="{case_url}">TC-{case.pk}: {case.summary}</a>',
                html=True,
            )

    def test_post_creates_new_run(self):
        new_run_summary = "TestRun summary"

        post_data = {
            "summary": new_run_summary,
            "plan": self.plan.pk,
            "product_id": self.plan.product_id,
            "product": self.plan.product_id,
            "build": self.build.pk,
            "manager": self.tester.email,
            "default_tester": self.tester.email,
            "notes": "",
            "case": [self.case_1.pk, self.case_2.pk],
        }

        url = reverse("testruns-new")
        response = self.client.post(url, post_data)

        new_run = TestRun.objects.last()

        self.assertRedirects(response, reverse("testruns-get", args=[new_run.pk]))

        for case, execution in zip(
            (self.case_1, self.case_2), new_run.executions.order_by("case")
        ):
            self.assertEqual(case, execution.case)
            self.assertIsNone(execution.tested_by)
            self.assertEqual(self.tester, execution.assignee)
            self.assertEqual(
                case.history.latest().history_id, execution.case_text_version
            )
            self.assertEqual(new_run.build, execution.build)
            self.assertIsNone(execution.stop_date)


class TestCloneRunView(PermissionsTestCase):
    permission_label = "testruns.add_testrun"
    http_method_names = ["get"]

    @classmethod
    def setUpTestData(cls):
        cls.test_run = TestRunFactory()
        cls.execution_1 = TestExecutionFactory(run=cls.test_run)
        cls.execution_2 = TestExecutionFactory(run=cls.test_run)

        cls.url = reverse("testruns-clone", args=[cls.test_run.pk])

        super().setUpTestData()

    def verify_get_with_permission(self):
        response = self.client.get(self.url)

        self.assertContains(response, _("Clone TestRun"))

        _clone_of = _("Clone of ")
        self.assertContains(
            response,
            '<input id="id_summary" class="form-control" name="summary" '
            f'type="text" value="{_clone_of}{self.test_run.summary}" required>',
            html=True,
        )

        for execution in (self.execution_1, self.execution_2):
            case_url = reverse("testcases-get", args=[execution.case.pk])

            self.assertContains(
                response,
                f'<a href="{case_url}">TC-{execution.case.pk}: {execution.case.summary}</a>',
                html=True,
            )


class TestSearchRuns(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super(TestSearchRuns, cls).setUpTestData()

        cls.search_runs_url = reverse("testruns-search")
        user_should_have_perm(cls.tester, "testruns.view_testrun")

    def test_search_page_is_shown(self):
        response = self.client.get(self.search_runs_url)
        self.assertContains(response, '<input id="id_summary" type="text"')

    def test_search_page_is_shown_with_get_parameter_used(self):
        response = self.client.get(self.search_runs_url, {"product": self.product.pk})
        self.assertContains(
            response,
            f'<option value="{self.product.pk}" selected>{self.product.name}</option>',
            html=True,
        )


class TestRunCasesMenu(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user_should_have_perm(cls.tester, "testruns.view_testrun")

        cls.url = reverse("testruns-get", args=[cls.test_run.pk])

        _update_text_version = _("Update text version")
        cls.update_text_version_html = f"""
            <a href="#" class="update-case-text-bulk">
                <span class="fa fa-refresh"></span>{_update_text_version}
            </a>
        """

        _assignee = _("Assignee")
        cls.change_assignee_html = f"""
            <a class="change-assignee-bulk" href="#">
                <span class="fa pficon-user"></span>
                {_assignee}
            </a>
        """

        _delete = _("Delete")
        cls.remove_executions_html = f"""
            <a class="bg-danger remove-execution-bulk" href="#">
                <span class="fa fa-trash-o"></span>
                {_delete}
            </a>
        """

    def test_add_cases_to_run_with_permission(self):
        user_should_have_perm(self.tester, "testruns.add_testexecution")
        response = self.client.get(self.url)
        self.assertContains(response, _("Search and add test cases"))
        self.assertContains(response, _("Advanced search"))

    def test_add_cases_to_run_without_permission(self):
        remove_perm_from_user(self.tester, "testruns.add_testexecution")
        response = self.client.get(self.url)
        self.assertNotContains(response, _("Search and add test cases"))
        self.assertNotContains(response, _("Advanced search"))

    def test_change_assignee_with_permission(self):
        user_should_have_perm(self.tester, "testruns.change_testexecution")
        response = self.client.get(self.url)
        self.assertContains(response, self.change_assignee_html, html=True)

    def test_change_assignee_without_permission(self):
        remove_perm_from_user(self.tester, "testruns.change_testexecution")
        response = self.client.get(self.url)
        self.assertNotContains(response, self.change_assignee_html, html=True)

    def test_update_text_version_with_permission(self):
        user_should_have_perm(self.tester, "testruns.change_testexecution")
        response = self.client.get(self.url)
        self.assertContains(response, self.update_text_version_html, html=True)

    def test_update_text_version_without_permission(self):
        remove_perm_from_user(self.tester, "testruns.change_testexecution")
        response = self.client.get(self.url)
        self.assertNotContains(response, self.update_text_version_html, html=True)

    def test_remove_executions_with_permission(self):
        user_should_have_perm(self.tester, "testruns.delete_testexecution")
        response = self.client.get(self.url)
        self.assertContains(response, self.remove_executions_html, html=True)

    def test_remove_executions_without_permission(self):
        remove_perm_from_user(self.tester, "testruns.delete_testexecution")
        response = self.client.get(self.url)
        self.assertNotContains(response, self.remove_executions_html, html=True)


class TestRunStatusMenu(BaseCaseRun):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.url = reverse("testruns-get", args=[cls.test_run.pk])
        user_should_have_perm(cls.tester, "testruns.view_testrun")
        cls.status_menu_html = []

    def test_get_status_options_with_permission(self):
        user_should_have_perm(self.tester, "testruns.change_testexecution")
        response = self.client.get(self.url)
        self.assertEqual(HTTPStatus.OK, response.status_code)

        for execution_status in TestExecutionStatus.objects.all():
            self.assertContains(
                response,
                f'<span class="{execution_status.icon}"></span>{execution_status.name}',
                html=True,
            )

    def test_get_status_options_without_permission(self):
        remove_perm_from_user(self.tester, "testruns.change_testexecution")
        response = self.client.get(self.url)
        self.assertEqual(HTTPStatus.OK, response.status_code)

        for execution_status in TestExecutionStatus.objects.all():
            self.assertNotContains(
                response,
                f'<span class="{execution_status.icon}"></span>{execution_status.name}',
                html=True,
            )
