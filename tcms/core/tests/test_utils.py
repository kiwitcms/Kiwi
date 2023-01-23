import unittest
from unittest.mock import patch

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from tcms.core.utils.mailto import mailto


class TestMailTo(unittest.TestCase):
    def setUp(self):
        self.expected_subject = "Test Subject"
        self.expected_body = "Body text"
        self.expected_sender = "kiwi@example.com"
        self.expected_recipients = None

    @property
    def expected_kwargs(self):
        return {
            "target": send_mail,
            "args": (
                settings.EMAIL_SUBJECT_PREFIX + self.expected_subject,
                self.expected_body,
                self.expected_sender,
                self.expected_recipients,
            ),
            "kwargs": {"fail_silently": False},
            "daemon": True,
        }

    @patch("threading.Thread")
    def test_string_recipient(self, mock):
        self.expected_recipients = ["example@example.com"]
        mailto(
            template_name=None,
            subject="Test Subject",
            recipients="example@example.com",
            context="Body text",
        )
        mock.assert_called_once_with(**self.expected_kwargs)

    @patch("threading.Thread")
    def test_duplicate_recipients(self, mock):
        self.expected_recipients = ["example@example.com"]
        mailto(
            template_name=None,
            subject="Test Subject",
            recipients=["example@example.com", "example@example.com"],
            context="Body text",
        )
        mock.assert_called_once_with(**self.expected_kwargs)

    @patch("threading.Thread")
    def test_cc_email(self, mock):
        self.expected_recipients = ["example@example.com", "cc@example.com"]
        mailto(
            template_name=None,
            subject="Test Subject",
            recipients="example@example.com",
            context="Body text",
            cc=["cc@example.com"],
        )
        mock.assert_called_once_with(**self.expected_kwargs)

    @patch("django.conf.settings.DEBUG", True)
    @patch("django.conf.settings.ADMINS", [("Admin", "admin@example.com")])
    @patch("threading.Thread")
    def test_admin_email_on_debug(self, mock):
        self.expected_recipients = ["example@example.com", "admin@example.com"]
        mailto(
            template_name=None,
            subject="Test Subject",
            recipients="example@example.com",
            context="Body text",
        )
        mock.assert_called_once_with(**self.expected_kwargs)

    @patch("threading.Thread")
    def test_template(self, mock):
        template_name = "email/user_registered/notify_admins.txt"
        context = {
            "username": "username",
            "user_url": "https://example.com/username/",
        }
        self.expected_body = render_to_string(template_name, context)
        self.expected_recipients = ["example@example.com"]
        mailto(
            template_name=template_name,
            subject="Test Subject",
            recipients=["example@example.com"],
            context=context,
        )
        mock.assert_called_once_with(**self.expected_kwargs)
