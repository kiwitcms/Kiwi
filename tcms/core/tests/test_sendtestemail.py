import socket

from django.core.management import call_command
from django.test import TestCase, override_settings


class TestSendTestEmail(TestCase):
    """Test manage.py sendtestemail command"""

    @override_settings(EMAIL_HOST='bogus.nonexistent',
                       EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend')
    def test_send_false_server(self):
        """test command with fake SMTP server"""
        with self.assertRaises(socket.gaierror):
            call_command('sendtestemail', 'user@server')
