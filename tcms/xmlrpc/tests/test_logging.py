# -*- coding: utf-8 -*-
from mock import patch

from tcms.xmlrpc.models import XmlRpcLog
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestXMLRPCLogging(XmlrpcAPIBaseTest):
    @patch('tcms.xmlrpc.handlers.settings.DEBUG', new=False)
    def test_logging_with_authenticated_user(self):
        log_count = XmlRpcLog.objects.filter(user=self.api_user, method='Env.filter_groups').count()

        self.rpc_client.Env.filter_groups({})
        new_count = XmlRpcLog.objects.filter(user=self.api_user, method='Env.filter_groups').count()

        self.assertEqual(new_count, log_count + 1)

    @patch('tcms.xmlrpc.handlers.settings.DEBUG', new=False)
    def test_logging_with_anonymous_user(self):
        log_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Env.filter_groups').count()

        self.rpc_client.Auth.logout()
        self.rpc_client.Env.filter_groups({})
        new_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Env.filter_groups').count()

        self.assertEqual(new_count, log_count + 1)
