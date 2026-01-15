# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, objects-update-used

from datetime import datetime

import tcms_api
from attachments.models import Attachment
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _

from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testcases.models import TestCaseStatus
from tcms.testruns.models import TestExecution, TestRun, TestRunCC
from tcms.tests import remove_perm_from_user, user_should_have_perm
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
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestAddCase(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory(author=cls.api_user)

        cls.test_case = TestCaseFactory()
        cls.test_case.case_status = TestCaseStatus.objects.filter(
            is_confirmed=True
        ).first()
        cls.test_case.save()  # generate history object
        cls.plan.add_case(cls.test_case)

        cls.test_run = TestRunFactory(plan=cls.plan)

    def test_add_case(self):
        executions = self.rpc_client.TestRun.add_case(
            self.test_run.pk, self.test_case.pk
        )
        self.assertIsInstance(executions, list)

        for result in executions:
            self.assertIn("id", result)
            self.assertIn("assignee", result)
            self.assertEqual(result["tested_by"], None)
            self.assertIn("case_text_version", result)
            self.assertIn("start_date", result)
            self.assertIn("stop_date", result)
            self.assertIn("sortkey", result)
            self.assertEqual(result["run"], self.test_run.pk)
            self.assertEqual(result["case"], self.test_case.pk)
            self.assertIn("build", result)
            self.assertIn("status", result)
            self.assertIn("properties", result)
            self.assertIsInstance(result["properties"], list)

    def test_add_case_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password("api-testing")
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, "testruns.add_testexecution")

        rpc_client = tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            unauthorized_user.username,
            "api-testing",
        ).exec

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.add_case"'
        ):
            rpc_client.TestRun.add_case(self.test_run.pk, self.test_case.pk)

        exists = TestExecution.objects.filter(
            run=self.test_run.pk, case=self.test_case.pk
        ).exists()
        self.assertFalse(exists)


class TestRemovesCase(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory(author=cls.api_user)

        cls.test_case = TestCaseFactory()
        cls.test_case.save()  # generate history object
        cls.plan.add_case(cls.test_case)

        cls.test_run = TestRunFactory(plan=cls.plan)
        cls.test_execution = TestExecutionFactory(run=cls.test_run, case=cls.test_case)
        cls.test_execution.save()

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

        rpc_client = tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            unauthorized_user.username,
            "api-testing",
        ).exec

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.remove_case"'
        ):
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
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_case = TestCaseFactory()
        cls.test_case.case_status = TestCaseStatus.objects.filter(
            is_confirmed=True
        ).first()
        cls.test_case.save()
        cls.test_run = TestRunFactory()

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

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()

    def verify_api_with_permission(self):
        result = self.rpc_client.TestRun.get_cases(self.test_run.pk)
        self.assertTrue(isinstance(result, list))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.get_cases"'
        ):
            self.rpc_client.TestRun.get_cases(self.test_run.pk)


class TestAddTag(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory(author=cls.api_user)
        cls.build = BuildFactory(version=cls.plan.product_version)

        cls.test_runs = [
            TestRunFactory(
                build=cls.build,
                default_tester=None,
                plan=cls.plan,
            ),
            TestRunFactory(
                build=cls.build,
                default_tester=None,
                plan=cls.plan,
            ),
        ]

        cls.tag0 = TagFactory(name="xmlrpc_test_tag_0")
        cls.tag1 = TagFactory(name="xmlrpc_test_tag_1")

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

        rpc_client = tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            unauthorized_user.username,
            "api-testing",
        ).exec

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.add_tag"'
        ):
            rpc_client.TestRun.add_tag(self.test_runs[0].pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestRun.objects.filter(
            pk=self.test_runs[0].pk, tag__pk=self.tag0.pk
        ).exists()
        self.assertFalse(tag_exists)


class TestRemoveTag(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.product = ProductFactory()
        cls.version = VersionFactory(product=cls.product)
        cls.build = BuildFactory(version=cls.version)
        cls.plan = TestPlanFactory(author=cls.api_user, product=cls.product)

        cls.test_runs = [
            TestRunFactory(
                build=cls.build,
                default_tester=None,
                plan=cls.plan,
            ),
            TestRunFactory(
                build=cls.build,
                default_tester=None,
                plan=cls.plan,
            ),
        ]

        cls.tag0 = TagFactory(name="xmlrpc_test_tag_0")
        cls.tag1 = TagFactory(name="xmlrpc_test_tag_1")

        for tag in [cls.tag0, cls.tag1]:
            cls.test_runs[0].add_tag(tag)
            cls.test_runs[1].add_tag(tag)

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

        rpc_client = tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            unauthorized_user.username,
            "api-testing",
        ).exec

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.remove_tag"'
        ):
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


class TestRunCreate(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory(author=cls.api_user)
        cls.build = BuildFactory(version=cls.plan.product_version)

    def test_create_with_invalid_value(self):
        test_run_fields = {
            "plan": self.plan.pk,
            "build": self.build.pk,
            "summary": "TR without version",
            "manager": "manager",
        }

        with self.assertRaisesRegex(XmlRPCFault, 'Unknown user: "manager"'):
            self.rpc_client.TestRun.create(test_run_fields)


class TestCreatePermission(APIPermissionsTestCase):
    permission_label = "testruns.add_testrun"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory()
        cls.build = BuildFactory(version=cls.plan.product_version)

        cls.test_run_fields = {
            "plan": cls.plan.pk,
            "build": cls.build.pk,
            "summary": "TR created",
            "manager": UserFactory().pk,
            "start_date": "2020-05-05",
            "stop_date": "2020-05-05 10:00:00",
            "planned_start": "2020-05-05 09:00:00",
            "planned_stop": "2020-05-06",
        }

    def verify_api_with_permission(self):
        result = self.rpc_client.TestRun.create(self.test_run_fields)

        run_id = result["id"]
        test_run = TestRun.objects.get(pk=run_id)

        self.assertIn("id", result)
        self.assertEqual(result["summary"], self.test_run_fields["summary"])
        self.assertIn("notes", result)

        self.assertEqual(result["start_date"], datetime(2020, 5, 5))
        self.assertEqual(result["start_date"], test_run.start_date)

        self.assertEqual(result["stop_date"], test_run.stop_date)
        self.assertEqual(result["stop_date"], datetime(2020, 5, 5, 10, 0, 0))

        self.assertEqual(result["planned_start"], test_run.planned_start)
        self.assertEqual(result["planned_start"], datetime(2020, 5, 5, 9, 0, 0))

        self.assertEqual(result["planned_stop"], test_run.planned_stop)
        self.assertEqual(result["planned_stop"], datetime(2020, 5, 6))

        self.assertEqual(result["plan"], self.plan.pk)
        self.assertEqual(result["build"], self.build.pk)
        self.assertEqual(result["manager"], self.test_run_fields["manager"])
        self.assertIn("default_tester", result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.create"'
        ):
            self.rpc_client.TestRun.create(self.test_run_fields)


class TestCreateWithoutTimestamps(TestCreatePermission):
    def verify_api_with_permission(self):
        result = self.rpc_client.TestRun.create(
            {
                "plan": self.plan.pk,
                "build": self.build.pk,
                "summary": "TR created without timestamps",
                "manager": UserFactory().pk,
                # not specifying on purpose
                # start_date, stop_date, planned_start, planned_stop
            }
        )

        run_id = result["id"]
        test_run = TestRun.objects.get(pk=run_id)

        self.assertIsNone(result["start_date"])
        self.assertIsNone(test_run.start_date)

        self.assertIsNone(result["stop_date"])
        self.assertIsNone(test_run.stop_date)

        self.assertIsNone(result["planned_start"])
        self.assertIsNone(test_run.planned_start)

        self.assertIsNone(result["planned_stop"])
        self.assertIsNone(test_run.planned_stop)


class TestFilter(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory()

        cls.test_case = TestCaseFactory()
        cls.test_case.save()
        cls.plan.add_case(cls.test_case)

        cls.test_run = TestRunFactory(plan=cls.plan)

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
        self.assertEqual(result["build__version"], self.test_run.build.version.pk)
        self.assertEqual(
            result["build__version__value"],
            self.test_run.build.version.value,
        )
        self.assertEqual(
            result["build__version__product"], self.test_run.build.version.product.pk
        )
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
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.filter"'
        ):
            self.rpc_client.TestRun.filter(None)


class TestUpdateTestRun(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()

        cls.updated_test_plan = TestPlanFactory()
        cls.updated_build = BuildFactory()
        cls.updated_summary = "Updated summary."
        cls.updated_stop_date = datetime.strptime("2020-05-05", "%Y-%m-%d")
        cls.updated_planned_start = datetime.strptime(
            "2020-05-05 09:00:00", "%Y-%m-%d %H:%M:%S"
        )
        cls.updated_planned_stop = datetime.strptime("2020-05-06", "%Y-%m-%d")

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

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()
        cls.update_fields = {
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
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.update"'
        ):
            self.rpc_client.TestRun.update(self.test_run.pk, self.update_fields)


class TestListAttachmentsPermissions(APIPermissionsTestCase):
    permission_label = "attachments.view_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()

    def verify_api_with_permission(self):
        user_should_have_perm(self.tester, "attachments.add_attachment")
        self.rpc_client.TestRun.add_attachment(
            self.test_run.pk, "attachment.txt", "a2l3aXRjbXM="
        )
        remove_perm_from_user(self.tester, "attachments.add_attachment")

        attachments = self.rpc_client.TestRun.list_attachments(self.test_run.pk)
        self.assertEqual(1, len(attachments))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestRun.list_attachments"',
        ):
            self.rpc_client.TestRun.list_attachments(self.test_run.pk)


class TestListAttachmentsForUnknownId(TestListAttachmentsPermissions):
    def verify_api_with_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestRun matching query does not exist"
        ):
            self.rpc_client.TestRun.list_attachments(-1)


class TestAddAttachmentPermissions(APIPermissionsTestCase):
    permission_label = "attachments.add_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()

    def verify_api_with_permission(self):
        self.rpc_client.TestRun.add_attachment(
            self.test_run.pk, "test.txt", "a2l3aXRjbXM="
        )
        attachments = Attachment.objects.attachments_for_object(self.test_run)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].object_id, str(self.test_run.pk))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.add_attachment"'
        ):
            self.rpc_client.TestRun.add_attachment(
                self.test_run.pk, "test.txt", "a2l3aXRjbXM="
            )


class TestRemovePermissions(APIPermissionsTestCase):
    permission_label = "testruns.delete_testrun"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.run_1 = TestRunFactory()
        cls.run_2 = TestRunFactory()
        cls.run_3 = TestRunFactory()

        cls.query = {"pk__in": [cls.run_1.pk, cls.run_3.pk]}

    def verify_api_with_permission(self):
        num_deleted, _ = self.rpc_client.TestRun.remove(self.query)
        self.assertEqual(num_deleted, 2)
        self.assertFalse(TestRun.objects.filter(**self.query).exists())
        self.assertTrue(TestRun.objects.filter(pk=self.run_2.pk).exists())

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.remove"'
        ):
            self.rpc_client.TestRun.remove(self.query)

        self.assertTrue(TestRun.objects.filter(**self.query).exists())
        self.assertTrue(TestRun.objects.filter(pk=self.run_2.pk).exists())


class TestRunAddProperty(APIPermissionsTestCase):
    permission_label = "testruns.add_property"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()

    def verify_api_with_permission(self):
        result1 = self.rpc_client.TestRun.add_property(
            self.test_run.pk, "browser", "Firefox"
        )

        self.assertEqual(result1["run"], self.test_run.pk)
        self.assertEqual(result1["name"], "browser")
        self.assertEqual(result1["value"], "Firefox")

        # try adding again - should return existing value
        result2 = self.rpc_client.TestRun.add_property(
            self.test_run.pk, "browser", "Firefox"
        )
        self.assertEqual(result2["id"], result1["id"])
        self.assertEqual(result2["run"], self.test_run.pk)
        self.assertEqual(result2["name"], "browser")
        self.assertEqual(result2["value"], "Firefox")

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestRun.add_property"'
        ):
            self.rpc_client.TestRun.add_property(self.test_run.pk, "browser", "Chrome")


class TestRunGetCC(APIPermissionsTestCase):
    permission_label = "testruns.view_testrun"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.test_run = TestRunFactory()
        cls.user = UserFactory()

        TestRunCC.objects.get_or_create(
            run=cls.test_run,
            user=cls.user,
        )

        TestRunCC.objects.get_or_create(
            run=cls.test_run,
            user=cls.tester,
        )

    def verify_api_with_permission(self):
        result = self.rpc_client.TestRun.get_cc(self.test_run.pk)
        self.assertIn(self.user.email, result)
        self.assertIn(self.tester.email, result)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestRun.get_cc"',
        ):
            self.rpc_client.TestRun.get_cc(self.test_run.pk)
