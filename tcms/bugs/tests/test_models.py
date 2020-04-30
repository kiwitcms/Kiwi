# pylint: disable=wrong-import-position
import unittest

from django.conf import settings

if 'tcms.bugs.apps.AppConfig' not in settings.INSTALLED_APPS:
    raise unittest.SkipTest('tcms.bugs is disabled')

from django.template.loader import render_to_string     # noqa: E402
from django.test import TestCase                        # noqa: E402
from django.utils.translation import gettext_lazy as _  # noqa: E402
from mock import patch                                  # noqa: E402

from tcms.tests.factories import UserFactory            # noqa: E402
from tcms.bugs.tests.factory import BugFactory          # noqa: E402


class TestSendMailOnAssigneeChange(TestCase):
    """Test that assignee is notified by mail each time they are assigned a bug.

    Ideally, notifications are sent out when:
    * Assignee is assigned bug on bug creation
    * Assignee is assigned bug which was previously assigned to someone other assignee
    """

    @patch('tcms.core.utils.mailto.send_mail')
    def test_notify_assignee_on_bug_creation(self, send_mail):
        assignee = UserFactory()
        bug = BugFactory(assignee=assignee)

        expected_subject = _('NEW: Bug #%(pk)d - %(summary)s') % {'pk': bug.pk,
                                                                  'summary': bug.summary}
        expected_body = render_to_string('email/post_bug_save/email.txt', {'bug': bug})
        expected_recipients = [assignee.email]

        send_mail.assert_called_once_with(
            settings.EMAIL_SUBJECT_PREFIX + expected_subject,
            expected_body,
            settings.DEFAULT_FROM_EMAIL,
            expected_recipients,
            fail_silently=False
        )
        self.assertTrue(send_mail.called)

    @patch('tcms.core.utils.mailto.send_mail')
    def test_no_notification_if_assignee_not_set(self, send_mail):
        BugFactory(assignee=None)

        self.assertFalse(send_mail.called)
