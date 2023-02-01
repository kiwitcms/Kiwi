# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, too-many-ancestors

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms import tests
from tcms.testcases.models import TestCaseStatus
from tcms.testruns.models import TestRun
from tcms.tests import PermissionsTestCase, factories, user_should_have_perm


class EditTestRunViewTestCase(PermissionsTestCase):
    """Test permissions for TestRun edit action"""

    permission_label = "testruns.change_testrun"
    http_method_names = ["get", "post"]

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory(summary="Old summary")
        cls.url = reverse("testruns-edit", args=[cls.test_run.pk])
        cls.new_build = factories.BuildFactory(
            name="FastTest", version=cls.test_run.plan.product_version
        )
        intern = factories.UserFactory(username="intern", email="intern@example.com")
        cls.post_data = {
            "summary": "New run summary",
            "build": cls.new_build.pk,
            "manager": cls.test_run.manager.email,
            "default_tester": intern.email,
            "notes": "New run notes",
            "product_version": cls.test_run.plan.product_version.pk,
            "plan": cls.test_run.plan.pk,
        }
        super().setUpTestData()

    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assertContains(
            response,
            f'<input type="text" id="id_summary" name="summary" value="{self.test_run.summary}"'
            ' class="form-control" required>',
            html=True,
        )
        _username_or_email = _("Username or email")
        self.assertContains(
            response,
            f'<input id="id_manager" name="manager" value="{self.test_run.manager}"'
            ' type="text" class="form-control" placeholder='
            f'"{_username_or_email}" required>',
            html=True,
        )
        self.assertContains(response, _("Edit TestRun"))
        self.assertContains(response, "js/bundle.js")

    def verify_post_with_permission(self):
        user_should_have_perm(self.tester, "testruns.view_testrun")

        response = self.client.post(self.url, self.post_data)
        self.test_run.refresh_from_db()

        self.assertEqual(self.test_run.summary, "New run summary")
        self.assertEqual(self.test_run.build, self.new_build)
        self.assertEqual(self.test_run.notes, "New run notes")
        self.assertRedirects(response, reverse("testruns-get", args=[self.test_run.pk]))


class TestNewRunViewTestCase(tests.PermissionsTestCase):
    permission_label = "testruns.add_testrun"
    http_method_names = ["post", "get"]
    url = reverse("testruns-new")

    @classmethod
    def setUpTestData(cls):
        cls.plan = factories.TestPlanFactory()

        cls.build_fast = factories.BuildFactory(
            name="fast", version=cls.plan.product_version
        )

        cls.post_data = {
            "summary": cls.plan.name,
            "plan": cls.plan.pk,
            "build": cls.build_fast.pk,
            "notes": "Create new test run",
        }

        super().setUpTestData()

        cls.post_data["manager"] = cls.tester.email
        cls.post_data["default_tester"] = cls.tester.email

        case_status_confirmed = TestCaseStatus.objects.filter(is_confirmed=True).first()

        cls.case_1 = factories.TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=case_status_confirmed,
            plan=[cls.plan],
        )
        cls.case_1.save()  # will generate history object

        cls.case_2 = factories.TestCaseFactory(
            author=cls.tester,
            default_tester=None,
            reviewer=cls.tester,
            case_status=case_status_confirmed,
            plan=[cls.plan],
        )
        cls.case_2.save()  # will generate history object

        cls.post_data["case"] = [cls.case_1.pk, cls.case_2.pk]

    def verify_get_with_permission(self):
        user_should_have_perm(self.tester, "testruns.view_testrun")

        response = self.client.get(self.url, {"p": self.plan.pk, "c": self.case_1.pk})

        self.assertContains(response, self.plan.name)
        self.assertContains(response, self.case_1.summary)

    def verify_post_with_permission(self):
        user_should_have_perm(self.tester, "testruns.view_testrun")

        response = self.client.post(self.url, self.post_data)
        last_run = TestRun.objects.last()

        self.assertRedirects(response, reverse("testruns-get", args=[last_run.pk]))

        self.assertEqual(self.plan.name, last_run.summary)
        self.assertEqual(self.plan, last_run.plan)
        self.assertEqual(None, last_run.stop_date)
        self.assertEqual("Create new test run", last_run.notes)
        self.assertEqual(self.build_fast, last_run.build)
        self.assertEqual(self.tester, last_run.manager)
        self.assertEqual(self.tester, last_run.default_tester)
        for case, execution in zip(
            (self.case_1, self.case_2), last_run.executions.order_by("case")
        ):
            self.assertEqual(case, execution.case)
            self.assertEqual(None, execution.tested_by)
            self.assertEqual(self.tester, execution.assignee)
            self.assertEqual(
                case.history.latest().history_id, execution.case_text_version
            )
            self.assertEqual(last_run.build, execution.build)
            self.assertEqual(None, execution.stop_date)


class MenuAddCommentItemTestCase(PermissionsTestCase):
    permission_label = "django_comments.add_comment"
    http_method_names = ["get"]

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory()

        cls.url = reverse("testruns-get", args=[cls.test_run.pk])
        super().setUpTestData()

        cls.add_comment_html = '<a href="#" class="add-comment-bulk">'
        user_should_have_perm(cls.tester, "testruns.view_testrun")

    def assert_on_testrun_page(self, response):
        self.assertContains(response, self.test_run.summary)
        self.assertContains(response, self.test_run.plan)
        self.assertContains(response, self.test_run.build)

    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertContains(response, self.add_comment_html, html=False)

    def verify_get_without_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertNotContains(response, self.add_comment_html, html=False)


class MenuAddHyperlinkBulkTestCase(PermissionsTestCase):
    permission_label = "linkreference.add_linkreference"
    http_method_names = ["get"]

    @classmethod
    def setUpTestData(cls):
        cls.test_run = factories.TestRunFactory()

        cls.url = reverse("testruns-get", args=[cls.test_run.pk])
        super().setUpTestData()

        cls.expected_html = '<a href="#" class="add-hyperlink-bulk"'
        user_should_have_perm(cls.tester, "testruns.view_testrun")

    def assert_on_testrun_page(self, response):
        self.assertContains(response, self.test_run.summary)
        self.assertContains(response, self.test_run.plan)
        self.assertContains(response, self.test_run.build)

    def verify_get_with_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertContains(response, self.expected_html, html=False)

    def verify_get_without_permission(self):
        response = self.client.get(self.url)
        self.assert_on_testrun_page(response)
        self.assertNotContains(response, self.expected_html, html=False)
