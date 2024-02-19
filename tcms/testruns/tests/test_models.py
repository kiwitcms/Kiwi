# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors

from django import test
from django.test import TestCase
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from mock import patch
from parameterized import parameterized

from tcms.testcases.models import Property as TestCaseProperty
from tcms.testruns.models import Property as TestRunProperty
from tcms.tests import BaseCaseRun
from tcms.tests.factories import TestCaseFactory, TestExecutionFactory, TestRunFactory


class Test_TestRun(BaseCaseRun):  # pylint: disable=invalid-name
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.empty_test_run = TestRunFactory(
            plan=cls.plan,
            manager=cls.tester,
            default_tester=cls.tester,
        )

    @patch("tcms.core.utils.mailto.send_mail")
    def test_send_mail_after_test_run_creation(self, send_mail):
        test_run = TestRunFactory(plan=self.plan)

        recipients = test_run.get_notify_addrs()

        # Verify notification mail
        self.assertIn(
            _("NEW: TestRun #%(pk)d - %(summary)s")
            % {"pk": test_run.pk, "summary": test_run.summary},
            send_mail.call_args_list[0][0][0],
        )
        for recipient in recipients:
            self.assertIn(recipient, send_mail.call_args_list[0][0][-1])


class TestRunMethods(test.TestCase):
    @staticmethod
    def deconstruct_matrix(matrix_iterator):
        result = []
        for prop_tuple in matrix_iterator:
            combos = []
            for prop in prop_tuple:
                combos.append(f"{prop.name}={prop.value}")
            result.append(combos)

        return result

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.test_run = TestRunFactory()
        cls.test_case = TestCaseFactory()
        # we need 1 version in the history
        cls.test_case.save()

    def test_create_execution_without_status(self):
        for execution in self.test_run.create_execution(self.test_case):
            self.assertEqual(execution.status.weight, 0)
            self.assertEqual(execution.status.name, _("IDLE"))

    def test_generate_full_matrix_with_2_dimensional_properties(self):
        test_run = TestRunFactory()
        test_case = TestCaseFactory()

        # properties assigned to TestRun (aka environment)
        for value in ["Linux", "MacOS", "Windows"]:
            TestRunProperty.objects.get_or_create(run=test_run, name="OS", value=value)

        # properties assigned to the test case
        for value in ["Chrome", "Firefox"]:
            TestCaseProperty.objects.get_or_create(
                case=test_case, name="Browser", value=value
            )

        properties = test_run.property_set.union(
            TestCaseProperty.objects.filter(case=test_case)
        )

        matrix = self.deconstruct_matrix(test_run.property_matrix(properties, "full"))
        self.assertEqual(len(matrix), 6)
        self.assertIn(["Browser=Chrome", "OS=Linux"], matrix)
        self.assertIn(["Browser=Chrome", "OS=MacOS"], matrix)
        self.assertIn(["Browser=Chrome", "OS=Windows"], matrix)
        self.assertIn(["Browser=Firefox", "OS=Linux"], matrix)
        self.assertIn(["Browser=Firefox", "OS=MacOS"], matrix)
        self.assertIn(["Browser=Firefox", "OS=Windows"], matrix)

    def test_generate_full_matrix_with_1_dimensional_property(self):
        test_run = TestRunFactory()
        test_case = TestCaseFactory()

        # properties assigned to TestRun (aka environment)
        for value in ["linux", "mac", "windows"]:
            TestRunProperty.objects.get_or_create(
                run=test_run, name="platform", value=value
            )

        # properties assigned to the test case
        for value in ["linux", "windows"]:
            TestCaseProperty.objects.get_or_create(
                case=test_case, name="platform", value=value
            )

        properties = test_run.property_set.union(
            TestCaseProperty.objects.filter(case=test_case)
        )

        matrix = self.deconstruct_matrix(test_run.property_matrix(properties, "full"))
        self.assertEqual(len(matrix), 3)
        self.assertIn(["platform=linux"], matrix)
        self.assertIn(["platform=mac"], matrix)
        self.assertIn(["platform=windows"], matrix)

    def test_generate_pairwise_matrix_with_3_dimensional_properties(self):
        test_run = TestRunFactory()
        test_case = TestCaseFactory(summary="Installation on RAID array")

        # properties assigned to the test case
        for raid_level in [0, 1, 4, 5, 6, 10, "linear"]:
            TestCaseProperty.objects.get_or_create(
                case=test_case, name="Raid Level", value=raid_level
            )
        for encryption in ["Yes", "No"]:
            TestCaseProperty.objects.get_or_create(
                case=test_case, name="Encryption", value=encryption
            )
        for mount_point in ["/", "/home"]:
            TestCaseProperty.objects.get_or_create(
                case=test_case, name="Mount Point", value=mount_point
            )

        # properties assigned to TestRun (aka environment)
        for cpu_arch in ["aarch64", "x86_64", "ppc64le"]:
            TestRunProperty.objects.get_or_create(
                run=test_run, name="CPU Arch", value=cpu_arch
            )
        for fedora_variant in ["Server", "Workstation"]:
            TestRunProperty.objects.get_or_create(
                run=test_run, name="Fedora Variant", value=fedora_variant
            )

        properties = test_run.property_set.union(
            TestCaseProperty.objects.filter(case=test_case)
        )
        matrix = self.deconstruct_matrix(
            test_run.property_matrix(properties, "pairwise")
        )
        # the 2 biggest dimensions control the max size of a pairwise matrix
        # in this case: CPU Arch * RAID Level == 3 * 7
        self.assertEqual(len(matrix), 21)


class TestExecutionActualDuration(TestCase):
    @parameterized.expand(
        [
            (
                "both_values_are_set",
                timezone.datetime(2021, 3, 22),
                timezone.datetime(2021, 3, 23),
                timezone.timedelta(days=1),
            ),
            ("both_values_are_none", None, None, None),
            ("start_date_is_none", None, timezone.datetime(2021, 3, 23), None),
            ("stop_date_is_none", timezone.datetime(2021, 3, 22), None, None),
        ]
    )
    def test_when(self, _name, start, stop, expected):
        execution = TestExecutionFactory(start_date=start, stop_date=stop)
        self.assertEqual(execution.actual_duration, expected)
