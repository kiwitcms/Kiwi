# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, no-member

from django.conf import settings
from django.template.loader import render_to_string
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from mock import patch
from datetime import timedelta

from tcms.core.history import history_email_for
from tcms.testcases.helpers.email import get_case_notification_recipients
from tcms.tests import BasePlanCase
from tcms.tests.factories import (
    ComponentFactory,
    TagFactory,
    TestCaseComponentFactory,
    TestCaseFactory,
    TestCaseTagFactory,
)


class SupportsCyrillic(TestCase):
    def test_create_testcase_with_cyrillic_works_issue_1770(self):
        # https://github.com/kiwitcms/Kiwi/issues/1770
        case = TestCaseFactory(summary="Това е тест на кирилица")
        case.save()

        case.refresh_from_db()
        self.assertTrue(case.summary.endswith("кирилица"))

class TestCaseCalculateExpectedDuration(TestCase):
    """Test TestCase.expected_duration"""

    def test_duration_is_calculated_correctly(self):
        case_random_duration = TestCaseFactory()
        setup_duration = case_random_duration.setup_duration
        testing_duration = case_random_duration.testing_duration
        expected = setup_duration + testing_duration

        case_random_duration.save()

        case_random_duration.refresh_from_db()
        self.assertEqual(case_random_duration.expected_duration, expected)

    def test_empty_setup_duration_is_calculated_correctly(self):
        case_empty_setup_duration = TestCaseFactory(setup_duration = None)
        testing_duration = case_empty_setup_duration.testing_duration
        case_empty_setup_duration.save()

        case_empty_setup_duration.refresh_from_db()
        self.assertEqual(case_empty_setup_duration.expected_duration, testing_duration)

    def test_empty_testing_duration_is_calculated_correctly(self):
        case_empty_testing_duration = TestCaseFactory(testing_duration = None)
        setup_duration = case_empty_testing_duration.setup_duration
        case_empty_testing_duration.save()

        case_empty_testing_duration.refresh_from_db()
        self.assertEqual(case_empty_testing_duration.expected_duration, setup_duration)

    def test_empty_durations_are_calculated_correctly(self):
        case_no_durations = TestCaseFactory(setup_duration = None, testing_duration = None)
        case_no_durations.save()

        case_no_durations.refresh_from_db()
        self.assertEqual(case_no_durations.expected_duration, None)


class TestCaseRemoveComponent(BasePlanCase):
    """Test TestCase.remove_component"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveComponent, cls).setUpTestData()

        cls.component_1 = ComponentFactory(
            name="Application",
            product=cls.product,
            initial_owner=cls.tester,
            initial_qa_contact=cls.tester,
        )
        cls.component_2 = ComponentFactory(
            name="Database",
            product=cls.product,
            initial_owner=cls.tester,
            initial_qa_contact=cls.tester,
        )

        cls.cc_rel_1 = TestCaseComponentFactory(
            case=cls.case, component=cls.component_1
        )
        cls.cc_rel_2 = TestCaseComponentFactory(
            case=cls.case, component=cls.component_2
        )

    def test_remove_a_component(self):
        self.case.remove_component(self.component_1)

        found = self.case.component.filter(pk=self.component_1.pk).exists()
        self.assertFalse(
            found,
            "Component {0} exists. But, it should be removed.".format(
                self.component_1.pk
            ),
        )
        found = self.case.component.filter(pk=self.component_2.pk).exists()
        self.assertTrue(
            found,
            "Component {0} does not exist. It should not be removed.".format(
                self.component_2.pk
            ),
        )


class TestCaseRemoveTag(BasePlanCase):
    """Test TestCase.remove_tag"""

    @classmethod
    def setUpTestData(cls):
        super(TestCaseRemoveTag, cls).setUpTestData()

        cls.tag_rhel = TagFactory(name="rhel")
        cls.tag_fedora = TagFactory(name="fedora")
        TestCaseTagFactory(case=cls.case, tag=cls.tag_rhel)
        TestCaseTagFactory(case=cls.case, tag=cls.tag_fedora)

    def test_remove_tag(self):
        self.case.remove_tag(self.tag_rhel)

        tag_pks = list(self.case.tag.all().values_list("pk", flat=True))
        self.assertEqual([self.tag_fedora.pk], tag_pks)


class TestSendMailOnCaseIsUpdated(BasePlanCase):
    """Test send mail on case post_save signal is triggered"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.case.emailing.notify_on_case_update = True
        cls.case.emailing.auto_to_case_author = True
        cls.case.emailing.save()

    @patch("tcms.core.utils.mailto.send_mail")
    def test_send_mail_to_case_author(self, send_mail):
        self.case.summary = "New summary for running test"
        self.case.save()

        expected_subject, expected_body = history_email_for(
            self.case, self.case.summary
        )
        recipients = get_case_notification_recipients(self.case)

        # Verify notification mail
        send_mail.assert_called_once_with(
            settings.EMAIL_SUBJECT_PREFIX + expected_subject,
            expected_body,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )


class TestSendMailOnCaseIsDeleted(BasePlanCase):
    """Test send mail on case post_delete signal is triggered"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.case.emailing.notify_on_case_delete = True
        cls.case.emailing.auto_to_case_author = True
        cls.case.emailing.save()

    @patch("tcms.core.utils.mailto.send_mail")
    def test_send_mail_to_case_author(self, send_mail):
        expected_subject = _("DELETED: TestCase #%(pk)d - %(summary)s") % {
            "pk": self.case.pk,
            "summary": self.case.summary,
        }
        expected_body = render_to_string(
            "email/post_case_delete/email.txt", {"case": self.case}
        )
        recipients = get_case_notification_recipients(self.case)

        self.case.delete()

        # Verify notification mail
        send_mail.assert_called_once_with(
            settings.EMAIL_SUBJECT_PREFIX + expected_subject,
            expected_body,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
