# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init,too-many-lines

import unittest
from datetime import datetime, timedelta

import tcms_api
from attachments.models import Attachment
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.utils import timezone
from parameterized import parameterized

from tcms.core.helpers import comments
from tcms.management.models import Priority
from tcms.rpc.api.testcase import _validate_cc_list
from tcms.rpc.tests.utils import APIPermissionsTestCase, APITestCase
from tcms.testcases.models import Category, TestCase, TestCaseStatus
from tcms.tests import remove_perm_from_user
from tcms.tests.factories import (
    CategoryFactory,
    ComponentFactory,
    ProductFactory,
    TagFactory,
    TestCaseFactory,
    TestPlanFactory,
    UserFactory,
    VersionFactory,
)
from tcms.xmlrpc_wrapper import XmlRPCFault


class TestValidateEmail(unittest.TestCase):
    def test_non_list_email_collection(self):
        with self.assertRaisesRegex(TypeError, "cc_list should be a list object."):
            _validate_cc_list("example@example.com")

    def test_invalid_email(self):
        with self.assertRaises(ValidationError):
            _validate_cc_list(["@example.com"])

    def test_valid_email_list(self):  # pylint: disable=no-self-use
        _validate_cc_list(["example@example.com"])


class TestAddNotificationCCPermission(APIPermissionsTestCase):
    permission_label = "testcases.change_testcase"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.default_cc = "example@example.com"
        cls.testcase = TestCaseFactory()

    def verify_api_with_permission(self):
        self.rpc_client.TestCase.add_notification_cc(
            self.testcase.pk, [self.default_cc]
        )
        self.assertEqual(len(self.testcase.emailing.get_cc_list()), 1)
        self.assertEqual(self.testcase.emailing.get_cc_list(), [self.default_cc])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestCase.add_notification_cc"',
        ):
            self.rpc_client.TestCase.add_notification_cc(
                self.testcase.pk, [self.default_cc]
            )


class TestAddNotificationCC(APITestCase):
    def test_invalid_testcase_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestCase matching query does not exist"
        ):
            self.rpc_client.TestCase.add_notification_cc(-1, ["example@example.com"])


class TestGetNotificationCCPermission(APIPermissionsTestCase):
    permission_label = "testcases.view_testcase"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.default_cc = "example@example.com"
        cls.testcase = TestCaseFactory()
        cls.testcase.emailing.add_cc(cls.default_cc)

    def verify_api_with_permission(self):
        result = self.rpc_client.TestCase.get_notification_cc(self.testcase.pk)
        self.assertListEqual(result, [self.default_cc])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestCase.get_notification_cc"',
        ):
            self.rpc_client.TestCase.get_notification_cc(self.testcase.pk)


class TestGetNotificationCC(APITestCase):
    def test_invalid_testcase_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestCase matching query does not exist"
        ):
            self.rpc_client.TestCase.get_notification_cc(-1)


class TestRemoveNotificationCCPermission(APIPermissionsTestCase):
    permission_label = "testcases.change_testcase"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.default_cc = "example@example.com"
        cls.testcase = TestCaseFactory()
        cls.testcase.emailing.add_cc(cls.default_cc)

    def verify_api_with_permission(self):
        self.rpc_client.TestCase.remove_notification_cc(
            self.testcase.pk, [self.default_cc]
        )
        self.testcase.emailing.refresh_from_db()
        self.assertEqual([], self.testcase.emailing.get_cc_list())

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestCase.remove_notification_cc"',
        ):
            self.rpc_client.TestCase.remove_notification_cc(
                self.testcase.pk, [self.default_cc]
            )


class TestRemoveNotificationCC(APITestCase):
    def test_invalid_testcase_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestCase matching query does not exist"
        ):
            self.rpc_client.TestCase.remove_notification_cc(-1, ["example@example.com"])


class TestCaseFilter(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.tester = UserFactory(username="great tester")
        cls.product = ProductFactory(name="StarCraft")
        cls.version = VersionFactory(value="0.1", product=cls.product)
        cls.plan = TestPlanFactory(
            name="Test product.get_cases",
            author=cls.tester,
            product=cls.product,
            product_version=cls.version,
        )
        cls.case_category = CategoryFactory(product=cls.product)
        cls.cases_count = 10
        cls.cases = []
        for _ in range(cls.cases_count):
            test_case = TestCaseFactory(
                category=cls.case_category,
                author=cls.tester,
                reviewer=cls.tester,
                default_tester=None,
                plan=[cls.plan],
            )
            cls.cases.append(test_case)

    def test_filter_query_none(self):
        result = self.rpc_client.TestCase.filter()

        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)

        self.assertIn("id", result[0])
        self.assertIn("create_date", result[0])
        self.assertIn("is_automated", result[0])
        self.assertIn("script", result[0])
        self.assertIn("arguments", result[0])
        self.assertIn("extra_link", result[0])
        self.assertIn("summary", result[0])
        self.assertIn("requirement", result[0])
        self.assertIn("notes", result[0])
        self.assertIn("text", result[0])
        self.assertIn("case_status", result[0])
        self.assertIn("category", result[0])
        self.assertIn("priority", result[0])
        self.assertIn("author", result[0])
        self.assertIn("default_tester", result[0])
        self.assertIn("reviewer", result[0])
        self.assertIn("setup_duration", result[0])
        self.assertIn("testing_duration", result[0])
        self.assertIn("expected_duration", result[0])

    def test_filter_by_product_id(self):
        cases = self.rpc_client.TestCase.filter({"category__product": self.product.pk})
        self.assertIsNotNone(cases)
        self.assertEqual(len(cases), self.cases_count)

    @parameterized.expand(
        [
            ("both_values_are_not_set", {}, None, None, 0),
            (
                "setup_duration_is_not_set",
                {"testing_duration": timedelta(minutes=5)},
                None,
                300,
                300,
            ),
            (
                "testing_duration_is_not_set",
                {"setup_duration": timedelta(seconds=45)},
                45,
                None,
                45,
            ),
            (
                "both_values_are_set",
                {
                    "setup_duration": timedelta(seconds=45),
                    "testing_duration": timedelta(minutes=5),
                },
                45,
                300,
                345,
            ),
        ]
    )
    def test_duration_properties_in_result(
        self, _name, init_dict, setup_duration, testing_duration, expected_duration
    ):
        testcase = TestCaseFactory(**init_dict)
        result = self.rpc_client.TestCase.filter({"pk": testcase.pk})

        self.assertIsNotNone(result)
        self.assertEqual(result[0]["setup_duration"], setup_duration)
        self.assertEqual(result[0]["testing_duration"], testing_duration)
        self.assertEqual(result[0]["expected_duration"], expected_duration)


class TestUpdate(APITestCase):
    non_existing_username = "FakeUsername"
    non_existing_user_id = 999
    non_existing_email = "fake@email.com"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.testcase = TestCaseFactory(
            summary="Sanity test case", text="Given-When-Then", default_tester=None
        )
        cls.new_author = UserFactory()

    def test_update_text_and_product(self):
        author_pk = self.testcase.author.pk
        self.assertEqual("Sanity test case", self.testcase.summary)
        self.assertEqual("Given-When-Then", self.testcase.text)

        # update the test case
        result = self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "setup_duration": "1 10:00:00",
                "summary": "This was updated",
                "testing_duration": "00:01:00",
                "text": "new TC text",
            },
        )

        self.testcase.refresh_from_db()

        self.assertEqual(result["id"], self.testcase.pk)
        self.assertEqual("This was updated", self.testcase.summary)
        self.assertEqual("new TC text", self.testcase.text)
        # FK for author not passed above. Make sure it didn't change!
        self.assertEqual(author_pk, self.testcase.author.pk)

        self.assertIn("author", result)
        self.assertIn("create_date", result)
        self.assertIn("is_automated", result)
        self.assertIn("script", result)
        self.assertIn("arguments", result)
        self.assertIn("extra_link", result)
        self.assertIn("summary", result)
        self.assertIn("requirement", result)
        self.assertIn("notes", result)
        self.assertIn("setup_duration", result)
        self.assertIn("testing_duration", result)
        self.assertEqual(result["text"], self.testcase.text)
        self.assertEqual(result["case_status"], self.testcase.case_status.pk)
        self.assertEqual(result["category"], self.testcase.category.pk)
        self.assertEqual(result["priority"], self.testcase.priority.pk)
        self.assertEqual(str(self.testcase.setup_duration), "1 day, 10:00:00")
        self.assertEqual(self.testcase.testing_duration, timedelta(minutes=1))
        self.assertIn("default_tester", result)
        self.assertIn("reviewer", result)

    def test_update_author_issue_630(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        # update the test case
        updated = (
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "author": self.new_author.pk,
                },
            )
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.author)
        self.assertEqual(self.new_author.pk, updated["author"])

    def test_update_author_should_fail_for_non_existing_user_id(self):
        initial_author_id = self.testcase.author.pk
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "author": self.non_existing_user_id,
                },
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_author_id, self.testcase.author.pk)

    def test_update_author_accepts_username(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        # update the test case
        updated = (
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "author": self.new_author.username,
                },
            )
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.author)
        self.assertEqual(self.new_author.pk, updated["author"])

    def test_update_author_should_fail_for_non_existing_username(self):
        initial_author_username = self.testcase.author.username
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "author": self.non_existing_username,
                },
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_author_username, self.testcase.author.username)

    def test_update_author_accepts_email(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        # update the test case
        updated = (
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "author": self.new_author.email,
                },
            )
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.author)
        self.assertEqual(self.new_author.pk, updated["author"])

    def test_update_author_should_fail_for_non_existing_email(self):
        initial_author_email = self.testcase.author.email
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "author": self.non_existing_email,
                },
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_author_email, self.testcase.author.email)

    def test_update_priority_issue_1318(self):
        expected_priority = Priority.objects.exclude(
            pk=self.testcase.priority.pk
        ).first()

        self.assertNotEqual(expected_priority.pk, self.testcase.priority.pk)
        self.assertEqual("Sanity test case", self.testcase.summary)
        self.assertEqual("Given-When-Then", self.testcase.text)

        # update the test case
        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "priority": expected_priority.pk,
            },
        )

        self.testcase.refresh_from_db()

        # priority has changed
        self.assertEqual(expected_priority.pk, self.testcase.priority.pk)

        # but nothing else changed, issue #1318
        self.assertEqual("Sanity test case", self.testcase.summary)
        self.assertEqual("Given-When-Then", self.testcase.text)

    def test_update_default_tester_accepts_user_id(self):
        self.assertIsNone(self.testcase.default_tester)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "default_tester": self.new_author.pk,
            },
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.default_tester.pk)

    def test_update_default_tester_should_fail_with_non_existing_user_id(self):
        self.assertIsNone(self.testcase.default_tester)

        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "default_tester": self.non_existing_user_id,
                },
            )

        self.testcase.refresh_from_db()

        self.assertIsNone(self.testcase.default_tester)

    def test_update_default_tester_accepts_username(self):
        self.assertIsNone(self.testcase.default_tester)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "default_tester": self.new_author.username,
            },
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.default_tester.pk)

    def test_update_default_tester_should_fail_with_non_existing_username(self):
        self.assertIsNone(self.testcase.default_tester)

        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "default_tester": self.non_existing_username,
                },
            )

        self.testcase.refresh_from_db()

        self.assertIsNone(self.testcase.default_tester)

    def test_update_default_tester_accepts_email(self):
        self.assertIsNone(self.testcase.default_tester)
        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "default_tester": self.new_author.email,
            },
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.default_tester.pk)

    def test_update_default_tester_should_fail_with_non_existing_email(self):
        self.assertIsNone(self.testcase.default_tester)

        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "default_tester": self.non_existing_email,
                },
            )

        self.testcase.refresh_from_db()

        self.assertIsNone(self.testcase.default_tester)

    def test_update_reviewer_accepts_user_id(self):
        self.assertNotEqual(self.new_author, self.testcase.reviewer)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "reviewer": self.new_author.pk,
            },
        )

        self.testcase.refresh_from_db()

        self.assertEqual(self.new_author.pk, self.testcase.reviewer.pk)

    def test_update_reviewer_should_fail_with_non_existing_user_id(self):
        initial_reviewer_id = self.testcase.reviewer.pk
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "reviewer": self.non_existing_user_id,
                },
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_reviewer_id, self.testcase.reviewer.pk)

    def test_update_reviewer_accepts_username(self):
        self.assertNotEqual(self.new_author, self.testcase.reviewer)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "reviewer": self.new_author.username,
            },
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.reviewer)

    def test_update_reviewer_should_fail_for_non_existing_username(self):
        initial_reviewer_username = self.testcase.reviewer.username
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "reviewer": self.non_existing_username,
                },
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_reviewer_username, self.testcase.reviewer.username)

    def test_update_reviewer_accepts_email(self):
        self.assertNotEqual(self.new_author, self.testcase.author)

        self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
            self.testcase.pk,
            {
                "reviewer": self.new_author.email,
            },
        )

        self.testcase.refresh_from_db()
        self.assertEqual(self.new_author, self.testcase.reviewer)

    def test_update_reviewer_should_fail_for_non_existing_email(self):
        initial_reviewer_email = self.testcase.reviewer.email
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.update(  # pylint: disable=objects-update-used
                self.testcase.pk,
                {
                    "reviewer": self.non_existing_email,
                },
            )

        self.testcase.refresh_from_db()
        self.assertEqual(initial_reviewer_email, self.testcase.reviewer.email)


class TestCaseCreate(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        for _ in range(5):
            CategoryFactory()

    def test_passes_with_valid_data(self):
        result = self.rpc_client.TestCase.create(
            {
                "summary": "Newly created TC via API",
                "text": "Given-When-Then",
                "case_status": TestCaseStatus.objects.first().pk,
                "priority": Priority.objects.first().pk,
                "category": Category.objects.first().pk,
                "setup_duration": "2 20:10:00",
                "testing_duration": "00:00:30",
            }
        )

        tc_from_db = TestCase.objects.get(pk=result["id"])
        # author field is auto-configured if not passed
        self.assertEqual(result["author"], tc_from_db.author.pk)
        self.assertEqual(self.api_user, tc_from_db.author)

        self.assertIn("arguments", result)
        self.assertIn("create_date", result)
        self.assertGreater(result["create_date"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["create_date"], timezone.now() + timedelta(seconds=1))
        self.assertIn("default_tester", result)
        self.assertIn("extra_link", result)
        self.assertIn("is_automated", result)
        self.assertIn("notes", result)
        self.assertIn("requirement", result)
        self.assertIn("reviewer", result)
        self.assertIn("script", result)
        self.assertIn("setup_duration", result)
        self.assertIn("testing_duration", result)
        self.assertEqual(result["case_status"], tc_from_db.case_status.pk)
        self.assertEqual(result["category"], tc_from_db.category.pk)
        self.assertEqual(result["priority"], tc_from_db.priority.pk)
        self.assertEqual(result["summary"], tc_from_db.summary)
        self.assertEqual(result["text"], tc_from_db.text)
        self.assertEqual(str(tc_from_db.setup_duration), "2 days, 20:10:00")
        self.assertEqual(tc_from_db.testing_duration, timedelta(seconds=30))

    def test_author_can_be_specified(self):
        new_author = UserFactory()
        result = self.rpc_client.TestCase.create(
            {
                "summary": "TC via API with author",
                "case_status": TestCaseStatus.objects.last().pk,
                "priority": Priority.objects.last().pk,
                "category": Category.objects.last().pk,
                "author": new_author.pk,
            }
        )

        tc_from_db = TestCase.objects.get(pk=result["id"])

        self.assertEqual(result["id"], tc_from_db.pk)
        self.assertEqual(new_author, tc_from_db.author)

    def test_create_date_can_be_specified(self):
        result = self.rpc_client.TestCase.create(
            {
                "summary": "TC via API with author",
                "case_status": TestCaseStatus.objects.last().pk,
                "priority": Priority.objects.last().pk,
                "category": Category.objects.last().pk,
                "create_date": "2026-01-06 20:30:00",
            }
        )
        # create_date can be specified too
        self.assertEqual(result["create_date"], datetime(2026, 1, 6, 20, 30, 0))

        tc_from_db = TestCase.objects.get(pk=result["id"])

        self.assertEqual(result["id"], tc_from_db.pk)
        self.assertEqual(result["create_date"], tc_from_db.create_date)

    def test_fails_when_mandatory_fields_not_specified(self):
        with self.assertRaises(XmlRPCFault):
            self.rpc_client.TestCase.create(
                {
                    "summary": "TC via API without mandatory FK fields",
                }
            )


class TestRemovePermissions(APIPermissionsTestCase):
    permission_label = "testcases.delete_testcase"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.case_1 = TestCaseFactory()
        cls.case_2 = TestCaseFactory()
        cls.case_3 = TestCaseFactory()

        cls.query = {"pk__in": [cls.case_1.pk, cls.case_2.pk, cls.case_3.pk]}

    def verify_api_with_permission(self):
        num_deleted, _ = self.rpc_client.TestCase.remove(self.query)
        self.assertEqual(num_deleted, 3)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.remove"'
        ):
            self.rpc_client.TestCase.remove(self.query)


class TestAddTag(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.testcase = TestCaseFactory()

        cls.tag1 = TagFactory()
        cls.tag2 = TagFactory()

    def test_add_tag(self):
        self.rpc_client.TestCase.add_tag(self.testcase.pk, self.tag1.name)
        tag_exists = TestCase.objects.filter(
            pk=self.testcase.pk, tag__pk=self.tag1.pk
        ).exists()
        self.assertTrue(tag_exists)

    def test_add_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password("api-testing")
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, "testcases.add_testcasetag")

        rpc_client = tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            unauthorized_user.username,
            "api-testing",
        ).exec

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.add_tag"'
        ):
            rpc_client.TestCase.add_tag(self.testcase.pk, self.tag1.name)

        # tags were not modified
        tag_exists = TestCase.objects.filter(
            pk=self.testcase.pk, tag__pk=self.tag1.pk
        ).exists()
        self.assertFalse(tag_exists)


class TestRemoveTag(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.tag0 = TagFactory()
        cls.tag1 = TagFactory()

        cls.testcase = TestCaseFactory()
        cls.testcase.add_tag(cls.tag0)

    def test_remove_tag(self):
        self.rpc_client.TestCase.remove_tag(self.testcase.pk, self.tag0.name)
        tag_exists = TestCase.objects.filter(
            pk=self.testcase.pk, tag__pk=self.tag0.pk
        ).exists()
        self.assertFalse(tag_exists)

    def test_remove_tag_without_permissions(self):
        unauthorized_user = UserFactory()
        unauthorized_user.set_password("api-testing")
        unauthorized_user.save()

        unauthorized_user.user_permissions.add(*Permission.objects.all())
        remove_perm_from_user(unauthorized_user, "testcases.delete_testcasetag")

        rpc_client = tcms_api.TCMS(
            f"{self.live_server_url}/xml-rpc/",
            unauthorized_user.username,
            "api-testing",
        ).exec

        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.remove_tag"'
        ):
            rpc_client.TestCase.remove_tag(self.testcase.pk, self.tag0.name)

        # tags were not modified
        tag_exists = TestCase.objects.filter(
            pk=self.testcase.pk, tag__pk=self.tag0.pk
        ).exists()
        self.assertTrue(tag_exists)

        tag_exists = TestCase.objects.filter(
            pk=self.testcase.pk, tag__pk=self.tag1.pk
        ).exists()
        self.assertFalse(tag_exists)


class TestAddComponent(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        cls.test_case = TestCaseFactory()
        cls.good_component = ComponentFactory(product=cls.test_case.category.product)
        cls.bad_component = ComponentFactory()

    def test_add_component_from_same_product_is_allowed(self):
        result = self.rpc_client.TestCase.add_component(
            self.test_case.pk, self.good_component.name
        )
        self.assertEqual(result["id"], self.good_component.pk)
        self.assertEqual(result["name"], self.good_component.name)

    def test_add_component_from_another_product_is_not_allowed(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "Component matching query does not exist"
        ):
            self.rpc_client.TestCase.add_component(
                self.test_case.pk, self.bad_component.name
            )


class TestRemoveComponentPermission(APIPermissionsTestCase):
    permission_label = "testcases.delete_testcasecomponent"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()
        cls.test_case = TestCaseFactory()
        cls.good_component = ComponentFactory(product=cls.test_case.category.product)
        cls.bad_component = ComponentFactory(product=cls.test_case.category.product)
        cls.test_case.add_component(cls.good_component)
        cls.test_case.add_component(cls.bad_component)

    def verify_api_with_permission(self):
        self.rpc_client.TestCase.remove_component(
            self.test_case.pk, self.bad_component.pk
        )
        result = self.test_case.component
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first(), self.good_component)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestCase.remove_component"',
        ):
            self.rpc_client.TestCase.remove_component(
                self.test_case.pk, self.good_component.pk
            )


class TestRemoveComponent(APITestCase):
    def test_invalid_testcase_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestCase matching query does not exist"
        ):
            self.rpc_client.TestCase.remove_component(-1, -1)


class TestCaseAddCommentFromRegularUser(APIPermissionsTestCase):
    permission_label = "django_comments.add_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.case = TestCaseFactory()

    def verify_api_with_permission(self):
        created_comment = self.rpc_client.TestCase.add_comment(
            self.case.pk, "Hello World!"
        )

        self.assertEqual(created_comment["comment"], "Hello World!")
        self.assertEqual(created_comment["is_public"], True)
        self.assertEqual(created_comment["object_pk"], self.case.pk)
        self.assertEqual(created_comment["user"], self.tester.pk)
        self.assertGreater(
            created_comment["submit_date"], timezone.now() - timedelta(seconds=5)
        )
        self.assertLess(
            created_comment["submit_date"], timezone.now() + timedelta(seconds=1)
        )

        result = comments.get_comments(self.case)
        self.assertEqual(1, result.count())

        first_comment = result.first()
        self.assertEqual("Hello World!", first_comment.comment)
        self.assertEqual("Hello World!", created_comment["comment"])

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.add_comment"'
        ):
            self.rpc_client.TestCase.add_comment(self.case.pk, "Hello World!")


class TestCaseAddCommentFromSuperUser(TestCaseAddCommentFromRegularUser):
    def verify_api_with_permission(self):
        self.tester.is_superuser = True
        self.tester.save()

        new_user = UserFactory()

        # try overriding comment author
        result = self.rpc_client.TestCase.add_comment(
            self.case.pk, "Hello World", new_user.pk
        )

        self.assertEqual(result["comment"], "Hello World")
        self.assertEqual(result["is_public"], True)
        self.assertEqual(result["object_pk"], self.case.pk)
        self.assertEqual(result["user"], new_user.pk)
        self.assertGreater(result["submit_date"], timezone.now() - timedelta(seconds=5))
        self.assertLess(result["submit_date"], timezone.now() + timedelta(seconds=1))

        # try overriding comment submit_date
        result = self.rpc_client.TestCase.add_comment(
            self.case.pk, "Happy Testing", new_user.pk, datetime(2026, 1, 4, 0, 0, 0)
        )

        self.assertEqual(result["comment"], "Happy Testing")
        self.assertEqual(result["object_pk"], self.case.pk)
        self.assertEqual(result["user"], new_user.pk)
        self.assertEqual(result["submit_date"], datetime(2026, 1, 4, 0, 0, 0))


class TestAddComment(APITestCase):
    def test_invalid_testcase_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestCase matching query does not exist"
        ):
            self.rpc_client.TestCase.add_comment(-1, "Hello World!")


class TestRemoveCommentPermissions(APIPermissionsTestCase):
    permission_label = "django_comments.delete_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.case = TestCaseFactory()
        cls.comment_1 = comments.add_comment([cls.case], "First one", cls.tester)[0]
        cls.comment_2 = comments.add_comment([cls.case], "Second one", cls.tester)[0]
        cls.comment_3 = comments.add_comment([cls.case], "Third one", cls.tester)[0]

    def verify_api_with_permission(self):
        # Remove a specific comment
        self.rpc_client.TestCase.remove_comment(self.case.pk, self.comment_1.pk)
        self.assertEqual(len(comments.get_comments(self.case)), 2)

        # Remove all comments
        self.rpc_client.TestCase.remove_comment(self.case.pk)
        self.assertEqual(len(comments.get_comments(self.case)), 0)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.remove_comment"'
        ):
            self.rpc_client.TestCase.remove_comment(self.case.pk)


class TestRemoveComment(APITestCase):
    def test_invalid_testcase_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestCase matching query does not exist"
        ):
            self.rpc_client.TestCase.remove_comment(-1)


class TestCaseSortkeysPermissions(APIPermissionsTestCase):
    permission_label = "testcases.view_testcase"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.plan = TestPlanFactory()

        # add TCs with non-standard sortkeys
        cls.case_1 = TestCaseFactory()
        cls.plan.add_case(cls.case_1, sortkey=5)

        cls.case_2 = TestCaseFactory()
        cls.plan.add_case(cls.case_2, sortkey=15)

        cls.case_3 = TestCaseFactory()
        cls.plan.add_case(cls.case_3, sortkey=25)

    def verify_api_with_permission(self):
        result = self.rpc_client.TestCase.sortkeys(
            {
                "plan": self.plan.pk,
            }
        )

        # note: keys are of type str()
        self.assertEqual(result[str(self.case_1.pk)], 5)
        self.assertEqual(result[str(self.case_2.pk)], 15)
        self.assertEqual(result[str(self.case_3.pk)], 25)

        # Test query None
        result = self.rpc_client.TestCase.sortkeys()
        self.assertIsNotNone(result)
        self.assertGreater(len(result), 0)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.sortkeys"'
        ):
            self.rpc_client.TestCase.sortkeys(
                {
                    "plan": self.plan.pk,
                }
            )


class TestCaseCommentPermissions(APIPermissionsTestCase):
    permission_label = "django_comments.view_comment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.case = TestCaseFactory()
        comments.add_comment([cls.case], "First one", cls.tester)
        comments.add_comment([cls.case], "Second one", cls.tester)

    def verify_api_with_permission(self):
        result = self.rpc_client.TestCase.comments(self.case.pk)

        self.assertEqual(2, len(result))

        # also takes case to verify functionality b/c the target
        # method under test is very simple
        self.assertEqual(result[0]["comment"], "First one")
        self.assertEqual(result[1]["comment"], "Second one")
        for entry in result:
            self.assertEqual(entry["object_pk"], str(self.case.pk))
            self.assertEqual(entry["user_id"], self.tester.pk)
            self.assertEqual(entry["user_name"], self.tester.username)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.comments"'
        ):
            self.rpc_client.TestCase.comments(self.case.pk)


class TestAddAttachmentPermissions(APIPermissionsTestCase):
    permission_label = "attachments.add_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.case = TestCaseFactory()

    def verify_api_with_permission(self):
        self.rpc_client.TestCase.add_attachment(
            self.case.pk, "test.txt", "a2l3aXRjbXM="
        )
        attachments = Attachment.objects.attachments_for_object(self.case)
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].object_id, str(self.case.pk))

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault, 'Authentication failed when calling "TestCase.add_attachment"'
        ):
            self.rpc_client.TestCase.add_attachment(
                self.case.pk, "test.txt", "a2l3aXRjbXM="
            )


class TestListAttachments(APITestCase):
    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.case = TestCaseFactory()

    def test_list_attachments(self):
        self.rpc_client.TestCase.add_attachment(
            self.case.pk, "attachment.txt", "a2l3aXRjbXM="
        )
        attachments = self.rpc_client.TestCase.list_attachments(self.case.pk)
        self.assertEqual(len(attachments), 1)

    def test_invalid_testcase_id(self):
        with self.assertRaisesRegex(
            XmlRPCFault, "TestCase matching query does not exist"
        ):
            self.rpc_client.TestCase.list_attachments(-1)


class TestListAttachmentPermissions(APIPermissionsTestCase):
    permission_label = "attachments.view_attachment"

    @classmethod
    def _fixture_setup(cls):
        super()._fixture_setup()

        cls.case = TestCaseFactory()

    def verify_api_with_permission(self):
        attachments = self.rpc_client.TestCase.list_attachments(self.case.pk)
        self.assertEqual(len(attachments), 0)

    def verify_api_without_permission(self):
        with self.assertRaisesRegex(
            XmlRPCFault,
            'Authentication failed when calling "TestCase.list_attachments"',
        ):
            self.rpc_client.TestCase.list_attachments(self.case.pk)
