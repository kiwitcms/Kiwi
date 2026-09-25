# -*- coding: utf-8 -*-
# pylint: disable=invalid-name

from http import HTTPStatus

from django import test
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from parameterized import parameterized

from tcms.testcases.models import TestCasePlan, TestCaseStatus
from tcms.testplans.models import TestPlan
from tcms.tests import BasePlanCase, user_should_have_perm
from tcms.tests.factories import (
    ClassificationFactory,
    PlanTypeFactory,
    ProductFactory,
    TestCaseFactory,
    TestPlanFactory,
    UserFactory,
    VersionFactory,
)


class BasePlanTest(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory(username="admin", email="admin@example.com")
        cls.user.set_password("admin")
        cls.user.is_superuser = True
        cls.user.is_staff = True
        cls.user.save()

        cls.classification = ClassificationFactory(name="Auto")
        cls.product = ProductFactory(name="Kiwi", classification=cls.classification)
        cls.product_version = VersionFactory(value="0.1", product=cls.product)
        cls.plan_type = PlanTypeFactory()

        cls.test_plan = TestPlanFactory(
            name="another test plan for testing",
            product_version=cls.product_version,
            author=cls.user,
            product=cls.product,
            type=cls.plan_type,
        )
        # add TestCases to plan with status CONFIRMED
        for _i in range(5):
            TestCaseFactory(
                plan=[cls.test_plan],
                case_status=TestCaseStatus.objects.get(name="CONFIRMED"),
            )

        # also add a few PROPOSED TestCases
        for _i in range(3):
            TestCaseFactory(plan=[cls.test_plan])

        cls.plan_id = cls.test_plan.pk
        cls.child_plan = TestPlanFactory(parent=cls.test_plan)

    def setUp(self):
        super().setUp()
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.user.username,
            password="admin",
        )


class PlanTests(BasePlanTest):
    def test_open_plans_search(self):
        location = reverse("plans-search")
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_search_page_is_shown_with_get_parameter_used(self):
        response = self.client.get(
            reverse("plans-search"), {"product": self.product.pk}
        )
        self.assertContains(
            response,
            f'<option value="{self.product.pk}" selected>{self.product.name}</option>',
            html=True,
        )

    def test_plan_details(self):
        location = reverse("test_plan_url", args=[self.plan_id])

        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_plan_edit(self):
        location = reverse("plan-edit", args=[self.plan_id])
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_plan_history(self):
        # note: history URL is generated on the fly and not accessible via name
        location = f"/admin/testplans/testplan/{self.plan_id}/history/"
        response = self.client.get(location)
        self.assertEqual(response.status_code, HTTPStatus.OK)


class TestPlanModel(test.TestCase):
    """Test some model operations directly without a view"""

    @classmethod
    def setUpTestData(cls):
        cls.plan_tester = UserFactory(username="tester")
        cls.plan_tester.set_password("password")
        cls.plan_tester.save()
        user_should_have_perm(cls.plan_tester, "testplans.view_testplan")

        cls.plan_1 = TestPlanFactory()
        cls.testcase_1 = TestCaseFactory()
        cls.testcase_2 = TestCaseFactory()

        cls.plan_1.add_case(cls.testcase_1)
        cls.plan_1.add_case(cls.testcase_2)

    def test_plan_delete_case(self):
        self.plan_1.delete_case(self.testcase_1)
        cases_left = TestCasePlan.objects.filter(plan=self.plan_1.pk)
        self.assertEqual(1, cases_left.count())
        self.assertEqual(self.testcase_2.pk, cases_left[0].case.pk)

    def test_add_cases_sortkey_autoincrement(self):
        """
        When you add new cases, each new case should get a sortkey of the
        highest sortkey in the database + 10.

        The first case should get sortkey 0. The offset between the sortkeys is
        to leave space to insert cases in between without having to update all
        cases.
        """

        plan = TestPlanFactory()

        for sequence_no in range(3):
            case_plan = plan.add_case(TestCaseFactory())
            self.assertEqual(sequence_no * 10, case_plan.sortkey)

        # Check if you can still specify a sortkey manually to insert a case in
        # between the other cases.
        case_plan = plan.add_case(TestCaseFactory(), sortkey=15)
        self.assertEqual(15, case_plan.sortkey)

    def test_get_full_url(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username, password="password"
        )
        test_plan_url = self.plan_1.get_full_url()
        response = self.client.get(test_plan_url, follow=True)

        self.assertIsNotNone(test_plan_url)
        self.assertNotEqual(test_plan_url[-1], "/")
        self.assertContains(response, self.plan_1.name)


class TestExtraLinkURLField(test.TestCase):
    @parameterized.expand(
        [
            ("http", "http://example.com"),
            ("https", "https://example.com"),
            ("ftp", "ftp://example.com"),
            ("ftps", "ftps://example.com"),
        ]
    )
    def test_extra_link_valid_schemes(self, _name, url):
        plan = TestPlanFactory(extra_link=url)
        plan.full_clean()
        self.assertEqual(plan.extra_link, url)

    @parameterized.expand(
        [
            ("javascript_colon", "javascript:alert(1)"),
            ("javascript_slash", "javascript://alert(1)"),
            ("invalid_scheme", "other://example.com"),
            ("no_scheme", "example.com"),
        ]
    )
    def test_extra_link_invalid_schemes(self, _name, url):
        plan = TestPlanFactory.build(extra_link=url)
        with self.assertRaises(ValidationError):
            plan.full_clean()


class TestCloneView(BasePlanCase):
    """Test case for the page which clones a plan"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.plan_tester = UserFactory()
        cls.plan_tester.set_password("password")
        cls.plan_tester.save()
        user_should_have_perm(cls.plan_tester, "testplans.add_testplan")
        user_should_have_perm(cls.plan_tester, "testplans.view_testplan")

    @test.override_settings(LANGUAGE_CODE="en")
    def test_open_clone_page_to_clone_one_plan(self):
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username, password="password"
        )

        response = self.client.get(reverse("plans-clone", args=[self.plan.pk]))

        _name = _("Name")
        self.assertContains(
            response,
            f'<label class="col-md-1 col-lg-1" for="id_name">{_name}</label>',
            html=True,
        )

        self.assertContains(
            response,
            f'<input type="text" id="id_name" name="name" value="{self.plan.make_cloned_name()}"'
            ' class="form-control" required>',
            html=True,
        )

        # the option to set the source TP as parent is pre-filled with its ID
        self.assertContains(response, f"Set TP-{self.plan.pk} as parent of new TP")

    def test_clone_page_does_not_clone_via_post(self):
        # the actual cloning is done by TestPlan.clone(), see tcms/rpc/api/testplan.py
        self.client.login(  # nosec:B106:hardcoded_password_funcarg
            username=self.plan_tester.username, password="password"
        )

        response = self.client.post(
            reverse("plans-clone", args=[self.plan.pk]),
            {"name": "cloned plan"},
        )

        self.assertEqual(HTTPStatus.METHOD_NOT_ALLOWED, response.status_code)
        self.assertFalse(TestPlan.objects.filter(name="cloned plan").exists())
