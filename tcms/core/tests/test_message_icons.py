# -*- coding: utf-8 -*-
import unittest
from django.contrib import messages
from django.contrib.messages.storage.base import Message
from tcms.core.templatetags.extra_filters import message_icon


class TestMessageIcons(unittest.TestCase):

    def test_error_message_icon(self):
        self.assertEqual(message_icon(Message(messages.ERROR, 'error')),
                         'pficon-error-circle-o')

    def test_warning_message_icon(self):
        self.assertEqual(message_icon(Message(messages.WARNING, 'warning')),
                         'pficon-warning-triangle-o')

    def test_success_message_icon(self):
        self.assertEqual(message_icon(Message(messages.SUCCESS, 'ok')),
                         'pficon-ok')

    def test_info_message_icon(self):
        self.assertEqual(message_icon(Message(messages.INFO, 'info')),
                         'pficon-info')
