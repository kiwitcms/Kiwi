# pylint: disable=wrong-import-position
import unittest

from django.conf import settings

if "tcms.bugs.apps.AppConfig" not in settings.INSTALLED_APPS:
    raise unittest.SkipTest("tcms.bugs is disabled")

from django.template.loader import render_to_string  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402
from mock import patch  # noqa: E402

from tcms.bugs.tests.factory import BugFactory  # noqa: E402
from tcms.core.helpers.comments import add_comment, get_comments  # noqa: E402
from tcms.tests import BaseCaseRun, user_should_have_perm  # noqa: E402
from tcms.tests.factories import UserFactory  # noqa: E402
from tcms.utils.permissions import initiate_user_with_default_setups  # noqa: E402


class TestSendMailOnNewComment(BaseCaseRun):
    """Test that assignee and reporter are notified by mail each time a comment is added.

    Ideally, notifications are sent out when:
    * A new comment is added to the bug.
    * Bug is closed.
    * Bug is reopened.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        initiate_user_with_default_setups(cls.tester)
        cls.comment_bug_url = reverse("bugs-comment")
        user_should_have_perm(cls.tester, "bugs.change_bug")

        cls.assignee = UserFactory()
        cls.url = reverse("bugs-comment")

    @patch("tcms.core.utils.mailto.send_mail")
    def test_email_sent_when_bug_closed(self, send_mail):
        bug = BugFactory(assignee=self.assignee, reporter=self.tester)
        self.client.post(
            self.url, {"bug": bug.pk, "text": "", "action": "close"}, follow=True
        )

        expected_body = render_to_string(
            "email/post_bug_save/email.txt",
            {"bug": bug, "comment": get_comments(bug).last()},
        )
        expected_recipients = [self.assignee.email, self.tester.email]
        expected_recipients.sort()

        expected_subject = _("Bug #%(pk)d - %(summary)s") % {
            "pk": bug.pk,
            "summary": bug.summary,
        }

        self.assertTrue(send_mail.called)
        self.assertEqual(
            settings.EMAIL_SUBJECT_PREFIX + expected_subject,
            send_mail.call_args.args[0],
        )
        self.assertEqual(expected_body, send_mail.call_args.args[1])
        self.assertEqual(settings.DEFAULT_FROM_EMAIL, send_mail.call_args.args[2])
        self.assertEqual(len(send_mail.call_args.args[3]), len(expected_recipients))
        self.assertIn(expected_recipients[0], send_mail.call_args.args[3])
        self.assertIn(expected_recipients[1], send_mail.call_args.args[3])

    @patch("tcms.core.utils.mailto.send_mail")
    def test_email_sent_when_bug_reopened(self, send_mail):
        bug = BugFactory(assignee=self.assignee, reporter=self.tester)
        bug.status = False
        bug.save()
        self.client.post(
            self.url, {"bug": bug.pk, "text": "", "action": "reopen"}, follow=True
        )

        expected_body = render_to_string(
            "email/post_bug_save/email.txt",
            {"bug": bug, "comment": get_comments(bug).last()},
        )
        expected_recipients = [self.assignee.email, self.tester.email]
        expected_recipients.sort()

        expected_subject = _("Bug #%(pk)d - %(summary)s") % {
            "pk": bug.pk,
            "summary": bug.summary,
        }

        self.assertTrue(send_mail.called)
        self.assertEqual(
            settings.EMAIL_SUBJECT_PREFIX + expected_subject,
            send_mail.call_args.args[0],
        )
        self.assertEqual(expected_body, send_mail.call_args.args[1])
        self.assertEqual(settings.DEFAULT_FROM_EMAIL, send_mail.call_args.args[2])
        self.assertEqual(len(send_mail.call_args.args[3]), len(expected_recipients))
        self.assertIn(expected_recipients[0], send_mail.call_args.args[3])
        self.assertIn(expected_recipients[1], send_mail.call_args.args[3])

    @patch("tcms.core.utils.mailto.send_mail")
    def test_email_sent_to_all_commenters(self, send_mail):
        bug = BugFactory(assignee=self.assignee, reporter=self.tester)
        commenter = UserFactory()
        tracker = UserFactory()
        add_comment([bug], _("*bug created*"), tracker)
        add_comment([bug], _("*bug created*"), commenter)

        expected_body = render_to_string(
            "email/post_bug_save/email.txt",
            {"bug": bug, "comment": get_comments(bug).last()},
        )
        expected_recipients = [
            self.assignee.email,
            self.tester.email,
            commenter.email,
            tracker.email,
        ]
        expected_recipients.sort()

        expected_subject = _("Bug #%(pk)d - %(summary)s") % {
            "pk": bug.pk,
            "summary": bug.summary,
        }

        self.assertTrue(send_mail.called)
        self.assertEqual(
            settings.EMAIL_SUBJECT_PREFIX + expected_subject,
            send_mail.call_args.args[0],
        )
        self.assertEqual(expected_body, send_mail.call_args.args[1])
        self.assertEqual(settings.DEFAULT_FROM_EMAIL, send_mail.call_args.args[2])
        self.assertEqual(len(send_mail.call_args.args[3]), len(expected_recipients))
        self.assertIn(expected_recipients[0], send_mail.call_args.args[3])
        self.assertIn(expected_recipients[1], send_mail.call_args.args[3])
