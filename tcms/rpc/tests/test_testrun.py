# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, objects-update-used
from datetime import datetime
from xmlrpc.client import Fault as XmlRPCFault
from xmlrpc.client import ProtocolError

from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from tcms_api import xmlrpc

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testcases.models import TestCaseStatus
from tcms.testruns.models import TestExecution, TestRun
from tcms.tests import remove_perm_from_user
from tcms.tests.factories import (
    BuildFactory,
    ProductFactory,
    TagFactory,
    TestCaseFactory,
    TestExecutionFactory,
    TestPlanFactory,
    TestRunFactory,
    UserFactory,
    VersionFactory,
)


class TestAddCase(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory(author=self.api_user)

        self.test_case = TestCaseFactory()
        self.test_case.case_status = TestCaseStatus.objects.filter(
            is_confirmed=True
        ).first()
        self.test_case.save()  # generate history object
        self.plan.add_case(self.test_case)

        self.test_run = TestRunFactory(plan=self.plan)

    def test_add_case(self):
        result = self.rpc_client.TestRun.add_case(self.test_run.pk, self.test_case.pk)
        self.assertTrue(isinstance(result, dict))

        execution = TestExecution.objects.get(
            run=self.test_run.pk, case=self.test_case.pk
        )

        self.assertEqual(result["id"], execution.pk)
        self.assertIn("assignee", result)
        self.assertEqual(result["tested_by"], None)
        self.assertIn("case_text_version", result)
        self.assertIn("close_date", result)
        self.assertIn("sortkey", result)
        self.assertEqual(result["run"], execution.run.pk)
        self.assertEqual(result["case"], execution.case.pk)
        self.assertIn("build", result)
        self.assertIn("status", result)

    def test_add_case_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password("api-testing")
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, "testruns.add_testexecution")

        rpc_client = xmlrpc.TCMSXmlrpc(
            unauthorized_user.username,
            "api-testing",
            "%s/xml-rpc/" % self.live_server_url,
        ).server

        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            rpc_client.TestRun.add_case(self.test_run.pk, self.test_case.pk)

        exists = TestExecution.objects.filter(
            run=self.test_run.pk, case=self.test_case.pk
        ).exists()
        self.assertFalse(exists)


class TestRemovesCase(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory(author=self.api_user)

        self.test_case = TestCaseFactory()
        self.test_case.save()  # generate history object
        self.plan.add_case(self.test_case)

        self.test_run = TestRunFactory(plan=self.plan)
        self.test_execution = TestExecutionFactory(
            run=self.test_run, case=self.test_case
        )
        self.test_execution.save()

    def test_nothing_change_if_invalid_case_passed(self):
        self.rpc_client.TestRun.remove_case(self.test_run.pk, 999999)
        self.test_execution.refresh_from_db()
        self.assertTrue(
            TestExecution.objects.filter(pk=self.test_execution.pk).exists()
        )
        self.assertEqual(1, TestExecution.objects.count())

    def test_nothing_change_if_invalid_run_passed(self):
        self.rpc_client.TestRun.remove_case(99999, self.test_case.pk)
        self.test_execution.refresh_from_db()
        self.assertTrue(
            TestExecution.objects.filter(pk=self.test_execution.pk).exists()
        )
        self.assertEqual(1, TestExecution.objects.count())

    def test_remove_case_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password("api-testing")
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, "testruns.delete_testexecution")

        rpc_client = xmlrpc.TCMSXmlrpc(
            unauthorized_user.username,
            "api-testing",
            "%s/xml-rpc/" % self.live_server_url,
        ).server

        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            rpc_client.TestRun.remove_case(self.test_run.pk, self.test_case.pk)

        exists = TestExecution.objects.filter(
            run=self.test_run.pk, case=self.test_case.pk
        ).exists()
        self.assertTrue(exists)

    def test_should_remove_an_execution(self):
        self.rpc_client.TestRun.remove_case(self.test_run.pk, self.test_case.pk)
        self.assertFalse(
            TestExecution.objects.filter(pk=self.test_execution.pk).exists()
        )


class TestGetCases(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.test_case = TestCaseFactory()
        self.test_case.case_status = TestCaseStatus.objects.filter(
            is_confirmed=True
        ).first()
        self.test_case.save()
        self.test_run = TestRunFactory()

    def test_get_empty_result_if_no_case_added(self):
        result = self.rpc_client.TestRun.get_cases(self.test_run.pk)
        self.assertEqual(0, len(result))

    def test_get_cases(self):
        self.test_run.create_execution(case=self.test_case)
        result = self.rpc_client.TestRun.get_cases(self.test_run.pk)
        self.assertEqual(1, len(result))

        case = result[0]

        self.assertEqual(case["id"], self.test_case.pk)
        self.assertIn("execution_id", case)
        self.assertIn("status", case)

        self.assertIn("create_date", case)
        self.assertIn("is_automated", case)
        self.assertIn("script", case)
        self.assertIn("arguments", case)
        self.assertIn("extra_link", case)
        self.assertIn("summary", case)
        self.assertIn("requirement", case)
        self.assertIn("notes", case)
        self.assertIn("text", case)
        self.assertIn("case_status", case)
        self.assertIn("category", case)
        self.assertIn("priority", case)
        self.assertIn("author", case)
        self.assertIn("default_tester", case)
        self.assertIn("reviewer", case)


class TestGetCasesPermission(APIPermissionsTestCase):
    permission_label = "testruns.view_testrun"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.test_run = TestRunFactory()

    def verify_api_with_permission(self):
        result = self.rpc_client.TestRun.get_cases(self.test_run.pk)
        self.assertTrue(isinstance(result, list))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.TestRun.get_cases(self.test_run.pk)


class TestAddTag(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.build = BuildFactory(version=self.version)
        self.plan = TestPlanFactory(author=self.api_user, product=self.product)

        self.test_runs = [
            TestRunFactory(
                product_version=self.version,
                build=self.build,
                default_tester=None,
                plan=self.plan,
            ),
            TestRunFactory(
                product_version=self.version,
                build=self.build,
                default_tester=None,
                plan=self.plan,
            ),
        ]

        self.tag0 = TagFactory(name="xmlrpc_test_tag_0")
        self.tag1 = TagFactory(name="xmlrpc_test_tag_1")

    def test_add_tag(self):
        result = self.rpc_client.TestRun.add_tag(self.test_runs[0].pk, self.tag0.name)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], self.tag0.pk)
        self.assertEqual(result[0]["name"], self.tag0.name)

        tag_exists = TestRun.objects.filter(
            pk=self.test_runs[0].pk, tag__pk=self.tag0.pk
        ).exists()
        self.assertTrue(tag_exists)

    def test_add_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password("api-testing")
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, "testruns.add_testruntag")

        rpc_client = xmlrpc.TCMSXmlrpc(
            unauthorized_user.username,
            "api-testing",
            "%s/xml-rpc/" % self.live_server_url,
        ).server

        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            rpc_client.TestRun.add_tag(self.test_runs[0].pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestRun.objects.filter(
            pk=self.test_runs[0].pk, tag__pk=self.tag0.pk
        ).exists()
        self.assertFalse(tag_exists)


class TestRemoveTag(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.build = BuildFactory(version=self.version)
        self.plan = TestPlanFactory(author=self.api_user, product=self.product)

        self.test_runs = [
            TestRunFactory(
                product_version=self.version,
                build=self.build,
                default_tester=None,
                plan=self.plan,
            ),
            TestRunFactory(
                product_version=self.version,
                build=self.build,
                default_tester=None,
                plan=self.plan,
            ),
        ]

        self.tag0 = TagFactory(name="xmlrpc_test_tag_0")
        self.tag1 = TagFactory(name="xmlrpc_test_tag_1")

        for tag in [self.tag0, self.tag1]:
            self.test_runs[0].add_tag(tag)
            self.test_runs[1].add_tag(tag)

    def test_remove_tag(self):
        result = self.rpc_client.TestRun.remove_tag(
            self.test_runs[0].pk, self.tag0.name
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], self.tag1.pk)
        self.assertEqual(result[0]["name"], self.tag1.name)

        tag_exists = TestRun.objects.filter(
            pk=self.test_runs[0].pk, tag__pk=self.tag0.pk
        ).exists()
        self.assertFalse(tag_exists)

        tag_exists = TestRun.objects.filter(
            pk=self.test_runs[0].pk, tag__pk=self.tag1.pk
        ).exists()
        self.assertTrue(tag_exists)

    def test_remove_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password("api-testing")
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, "testruns.delete_testruntag")

        rpc_client = xmlrpc.TCMSXmlrpc(
            unauthorized_user.username,
            "api-testing",
            "%s/xml-rpc/" % self.live_server_url,
        ).server

        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            rpc_client.TestRun.remove_tag(self.test_runs[0].pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestRun.objects.filter(
            pk=self.test_runs[0].pk, tag__pk=self.tag0.pk
        ).exists()
        self.assertTrue(tag_exists)

        tag_exists = TestRun.objects.filter(
            pk=self.test_runs[0].pk, tag__pk=self.tag1.pk
        ).exists()
        self.assertTrue(tag_exists)


class TestProductVersionWhenCreating(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.build = BuildFactory(version=self.version)
        self.plan = TestPlanFactory(
            author=self.api_user, product=self.product, product_version=self.version
        )

    def test_create_without_product_version(self):
        test_run_fields = {
            "plan": self.plan.pk,
            "build": self.build.pk,
            "summary": "TR without product_version",
            "manager": self.api_user.username,
        }

        result = self.rpc_client.TestRun.create(test_run_fields)
        self.assertEqual(result["product_version"], self.plan.product_version.pk)

    def test_create_with_product_version(self):
        version2 = VersionFactory()

        test_run_fields = {
            "plan": self.plan.pk,
            "build": self.build.pk,
            "summary": "TR with product_version",
            "manager": self.api_user.pk,
            "product_version": version2.pk,
        }

        result = self.rpc_client.TestRun.create(test_run_fields)
        # the result is still using product_version from TR.plan.product_version
        # not the one we specified above
        self.assertEqual(result["product_version"], self.plan.product_version.pk)

    def test_create_with_invalid_value(self):
        test_run_fields = {
            "plan": self.plan.pk,
            "build": self.build.pk,
            "summary": "TR without product_version",
            "manager": "manager",
        }

        err_msg = 'Unknown user: "manager"'
        with self.assertRaisesRegex(XmlRPCFault, err_msg):
            self.rpc_client.TestRun.create(test_run_fields)


class TestCreatePermission(APIPermissionsTestCase):
    permission_label = "testruns.add_testrun"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.product = ProductFactory()
        self.version = VersionFactory(product=self.product)
        self.build = BuildFactory(version=self.version)
        self.plan = TestPlanFactory(product=self.product, product_version=self.version)
        self.test_run_fields = {
            "plan": self.plan.pk,
            "build": self.build.pk,
            "summary": "TR created",
            "manager": UserFactory().pk,
        }

    def verify_api_with_permission(self):
        result = self.rpc_client.TestRun.create(self.test_run_fields)

        self.assertIn("id", result)
        self.assertIn("product_version", result)
        self.assertIn("start_date", result)
        self.assertIn("stop_date", result)
        self.assertIn("planned_start", result)
        self.assertIn("planned_stop", result)
        self.assertEqual(result["summary"], self.test_run_fields["summary"])
        self.assertIn("notes", result)
        self.assertEqual(result["plan"], self.plan.pk)
        self.assertEqual(result["build"], self.build.pk)
        self.assertEqual(result["manager"], self.test_run_fields["manager"])
        self.assertIn("default_tester", result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.TestRun.create(self.test_run_fields)


class TestFilter(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.plan = TestPlanFactory()

        self.test_case = TestCaseFactory()
        self.test_case.save()
        self.plan.add_case(self.test_case)

        self.test_run = TestRunFactory(plan=self.plan)

    def test_empty_query(self):
        result = self.rpc_client.TestRun.filter()
        self.assertTrue(isinstance(result, list))
        self.assertEqual(1, len(result))
        self.assertEqual(self.test_run.pk, result[0]["id"])

    def test_filter(self):
        _ = TestRunFactory()
        result = self.rpc_client.TestRun.filter({"plan": self.plan.pk})
        self.assertEqual(1, len(result))

        result = result[0]

        self.assertEqual(result["id"], self.test_run.pk)
        self.assertEqual(result["product_version"], self.test_run.product_version.pk)
        self.assertEqual(result["start_date"], self.test_run.start_date)
        self.assertEqual(result["stop_date"], self.test_run.stop_date)
        self.assertEqual(result["planned_start"], self.test_run.planned_start)
        self.assertEqual(result["planned_stop"], self.test_run.planned_stop)
        self.assertEqual(result["summary"], self.test_run.summary)
        self.assertEqual(result["notes"], self.test_run.notes)
        self.assertEqual(result["plan"], self.test_run.plan.pk)
        self.assertEqual(result["build"], self.test_run.build.pk)
        self.assertEqual(result["manager"], self.test_run.manager.pk)
        self.assertEqual(result["default_tester"], self.test_run.default_tester.pk)


class TestFilterPermission(APIPermissionsTestCase):
    permission_label = "testruns.view_testrun"

    def verify_api_with_permission(self):
        result = self.rpc_client.TestRun.filter()
        self.assertTrue(isinstance(result, list))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.TestRun.filter(None)


class TestUpdateTestRun(APITestCase):
    def _fixture_setup(self):
        super()._fixture_setup()

        self.test_run = TestRunFactory()

        self.updated_test_plan = TestPlanFactory()
        self.updated_build = BuildFactory()
        self.updated_summary = "Updated summary."
        self.updated_stop_date = datetime.strptime("2020-05-05", "%Y-%m-%d")
        self.updated_planned_start = datetime.strptime(
            "2020-05-05 09:00:00", "%Y-%m-%d %H:%M:%S"
        )
        self.updated_planned_stop = datetime.strptime("2020-05-06", "%Y-%m-%d")

    def test_successful_update(self):
        update_fields = {
            "plan": self.updated_test_plan.pk,
            "build": self.updated_build.pk,
            "summary": self.updated_summary,
            "stop_date": self.updated_stop_date,
            "planned_start": self.updated_planned_start,
            "planned_stop": self.updated_planned_stop,
        }

        # assert test run is not updated yet
        self.assertNotEqual(self.updated_test_plan, self.test_run.plan.name)
        self.assertNotEqual(self.updated_build, self.test_run.build.name)
        self.assertNotEqual(self.updated_summary, self.test_run.summary)
        self.assertNotEqual(self.updated_stop_date, self.test_run.stop_date)
        self.assertNotEqual(self.updated_planned_start, self.test_run.planned_start)
        self.assertNotEqual(self.updated_planned_stop, self.test_run.planned_stop)

        result = self.rpc_client.TestRun.update(self.test_run.pk, update_fields)
        self.test_run.refresh_from_db()

        # compare result, returned from API call with test run from DB
        self.assertEqual(result["id"], self.test_run.pk)
        self.assertEqual(result["product_version"], self.test_run.product_version.pk)
        self.assertEqual(result["start_date"], self.test_run.start_date)
        self.assertEqual(result["stop_date"], self.test_run.stop_date)
        self.assertEqual(result["planned_start"], self.test_run.planned_start)
        self.assertEqual(result["planned_stop"], self.test_run.planned_stop)
        self.assertEqual(result["summary"], self.test_run.summary)
        self.assertEqual(result["notes"], self.test_run.notes)
        self.assertEqual(result["plan"], self.test_run.plan.pk)
        self.assertEqual(result["build"], self.test_run.build.pk)
        self.assertEqual(result["manager"], self.test_run.manager.pk)
        self.assertEqual(result["default_tester"], self.test_run.default_tester.pk)

    def test_wrong_date_format(self):
        test_run = TestRunFactory()
        update_fields = {
            "plan": self.updated_test_plan.pk,
            "build": self.updated_build.pk,
            "summary": self.updated_summary,
            "stop_date": "10-10-2010",
            "planned_stop": "11-10-2010",
        }

        with self.assertRaisesMessage(
            Exception, str(_("Invalid date format. Expected YYYY-MM-DD [HH:MM:SS]."))
        ):
            self.rpc_client.TestRun.update(test_run.pk, update_fields)

        # assert test run fields have not been updated
        test_run.refresh_from_db()
        self.assertNotEqual(update_fields["plan"], test_run.plan.pk)
        self.assertNotEqual(update_fields["build"], test_run.build.pk)
        self.assertNotEqual(update_fields["summary"], test_run.summary)
        self.assertNotEqual(
            datetime.strptime(update_fields["stop_date"], "%d-%m-%Y"),
            test_run.stop_date,
        )
        self.assertNotEqual(
            datetime.strptime(update_fields["planned_stop"], "%d-%m-%Y"),
            test_run.planned_stop,
        )

    def test_update_with_product(self):
        test_run = TestRunFactory()
        product = ProductFactory()
        updated_test_plan = TestPlanFactory(product=product)
        updated_build = BuildFactory(version=product.version.first())
        updated_summary = "Updated summary."
        updated_stop_date = "2020-05-05 00:00:00"

        updated_test_run = self.rpc_client.TestRun.update(
            test_run.pk,
            {
                "plan": updated_test_plan.pk,
                "product": product.id,
                "build": updated_build.pk,
                "summary": updated_summary,
                "stop_date": updated_stop_date,
            },
        )

        test_run.refresh_from_db()

        self.assertEqual(updated_test_run["plan"], updated_test_plan.pk)
        self.assertEqual(updated_test_run["build"], updated_build.pk)
        self.assertEqual(updated_test_run["summary"], updated_summary)
        self.assertEqual(updated_test_run["stop_date"], test_run.stop_date)


class TestUpdatePermission(APIPermissionsTestCase):
    permission_label = "testruns.change_testrun"

    def _fixture_setup(self):
        super()._fixture_setup()

        self.test_run = TestRunFactory()
        self.update_fields = {
            "plan": TestPlanFactory().pk,
            "build": BuildFactory().pk,
            "summary": "Updated summary.",
            "stop_date": "2020-05-05 00:00:00",
        }

    def verify_api_with_permission(self):
        updated_test_run = self.rpc_client.TestRun.update(
            self.test_run.pk, self.update_fields
        )
        self.test_run.refresh_from_db()

        self.assertEqual(updated_test_run["summary"], self.update_fields["summary"])
        self.assertEqual(updated_test_run["stop_date"], self.test_run.stop_date)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(ProtocolError, "403 Forbidden"):
            self.rpc_client.TestRun.update(self.test_run.pk, self.update_fields)
