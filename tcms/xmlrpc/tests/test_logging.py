# -*- coding: utf-8 -*-
# pylint: disable=invalid-name, objects-update-used

from mock import patch

from django.db.models.functions import Length

from tcms.xmlrpc.models import XmlRpcLog
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestXMLRPCLogging(XmlrpcAPIBaseTest):
    def assertArgsNotLogged(self, rpc_method):
        # verify that arguments for specific RPC method are not logged
        log_count = XmlRpcLog.objects.annotate(
            args_len=Length('args')
        ).filter(
            method=rpc_method,
            args_len__gt=0
        ).count()
        self.assertEqual(0, log_count)

    @patch('tcms.xmlrpc.handlers.settings.DEBUG', new=False)
    def test_logging_with_authenticated_user(self):
        log_count = XmlRpcLog.objects.filter(user=self.api_user, method='Env.Group.filter').count()

        self.rpc_client.Env.Group.filter({})
        new_count = XmlRpcLog.objects.filter(user=self.api_user, method='Env.Group.filter').count()

        self.assertEqual(new_count, log_count + 1)

    @patch('tcms.xmlrpc.handlers.settings.DEBUG', new=False)
    def test_logging_with_anonymous_user(self):
        log_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Env.Group.filter').count()

        self.rpc_client.Auth.logout()
        self.rpc_client.Env.Group.filter({})
        new_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Env.Group.filter').count()

        self.assertEqual(new_count, log_count + 1)

    @patch('tcms.xmlrpc.handlers.settings.DEBUG', new=False)
    def test_dont_log_passwords(self):
        # the parent class will call Auth.login
        # sending the user password!
        self.assertArgsNotLogged('Auth.login')

        # also call User.update which accepts passwords via dict
        self.rpc_client.User.update(None, {
            'password': 'new-password',
            'old_password': 'api-testing',
        })
        self.assertArgsNotLogged('User.update')
