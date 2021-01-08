# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized

from tcms.testruns.models import TestExecutionStatus, TestRun
from tcms.tests import LoggedInTestCase
from tcms.tests.factories import TestRunFactory, UserFactory
from tcms.utils.permissions import initiate_user_with_default_setups


class TestTestRunAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)
        cls.test_run = TestRunFactory()

        cls.superuser = UserFactory()
        cls.superuser.is_superuser = True
        cls.superuser.set_password("password")
        cls.superuser.save()

    def test_regular_user_can_not_add_testrun(self):
        response = self.client.get(reverse("admin:testruns_testrun_add"))
        self.assertRedirects(response, reverse("admin:testruns_testrun_changelist"))

    def test_regular_user_can_not_change_testrun(self):
        response = self.client.get(
            reverse("admin:testruns_testrun_change", args=[self.test_run.pk])
        )
        self.assertRedirects(response, reverse("testruns-get", args=[self.test_run.pk]))

    def test_regular_user_can_not_delete_testrun(self):
        response = self.client.get(
            reverse("admin:testruns_testrun_delete", args=[self.test_run.pk]),
            follow=True,
        )
        self.assertContains(
            response, _("Permission denied: TestRun does not belong to you")
        )

    def test_superuser_can_delete_testrun(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.superuser.username, password="password"
        )
        response = self.client.get(
            reverse("admin:testruns_testrun_delete", args=[self.test_run.pk])
        )
        self.assertContains(response, _("Yes, I'm sure"))
        response = self.client.post(
            reverse("admin:testruns_testrun_delete", args=[self.test_run.pk]),
            {"post": "yes"},
            follow=True,
        )
        self.assertRedirects(response, reverse("admin:testruns_testrun_changelist"))
        self.assertEqual(TestRun.objects.filter(pk=self.test_run.pk).exists(), False)


class TestTestExecutionStatusAdmin(LoggedInTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        initiate_user_with_default_setups(cls.tester)

    def test_changelist_view_color_column(self):
        response = self.client.get(
            reverse("admin:testruns_testexecutionstatus_changelist")
        )
        self.assertContains(
            response,
            (
                """
            <span style="background-color: #92d400; height: 20px; display: block;
                         color: black; font-weight: bold">
                #92d400
            </span>
            """
            ),
        )

    def test_changelist_view_icon_column(self):
        response = self.client.get(
            reverse("admin:testruns_testexecutionstatus_changelist")
        )
        self.assertContains(
            response,
            (
                """
            <span class="fa fa-check-circle-o" style="font-size: 18px; color: #92d400;"></span>
            """
            ),
        )

    @parameterized.expand(
        [
            ("positive", TestExecutionStatus.objects.all().filter(weight__gt=0)),
            ("neural", TestExecutionStatus.objects.all().filter(weight=0)),
            ("negative", TestExecutionStatus.objects.all().filter(weight__lt=0)),
        ]
    )
    def test_test_execution_statuses_can_be_deleted_but_one_must_remain(
        self, _name, exe_statuses
    ):
        for exe_status in exe_statuses[1:]:
            response = self.client.get(
                reverse(
                    "admin:testruns_testexecutionstatus_delete", args=[exe_status.pk]
                )
            )
            self.assertContains(response, _("Yes, I'm sure"))
            response = self.client.post(
                reverse(
                    "admin:testruns_testexecutionstatus_delete", args=[exe_status.pk]
                ),
                {"post": "yes"},
                follow=True,
            )
            self.assertRedirects(
                response, reverse("admin:testruns_testexecutionstatus_changelist")
            )
            self.assertEqual(
                TestExecutionStatus.objects.filter(pk=exe_status.pk).exists(), False
            )

        exe_status = exe_statuses.first()
        response = self.client.get(
            reverse("admin:testruns_testexecutionstatus_delete", args=[exe_status.pk]),
            follow=True,
        )
        self.assertRedirects(
            response, reverse("admin:testruns_testexecutionstatus_changelist")
        )
        self.assertContains(
            response,
            _("1 negative, 1 neutral & 1 positive status required!"),
            html=True,
        )
