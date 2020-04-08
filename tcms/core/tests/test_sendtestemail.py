from django.core.management import call_command
from django.test import TestCase, override_settings
import socket


class TestSendTestEmail(TestCase):
    """Test manage.py sendtestemail command"""

    @override_settings(EMAIL_HOST = 'bogus.nonexistent')
    def test_send_false_server(self):
        """test command with fake SMTP server"""
        call_command('sendtestemail', '--admins')
        self.assertRaises(socket.gaierror)