# -*- coding: utf-8 -*-
from mock import patch
from django.contrib.auth.models import AnonymousUser

from tcms.xmlrpc.api import env
from tcms.xmlrpc.models import XmlRpcLog

from tcms.tests.factories import UserFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest
from tcms.xmlrpc.tests.utils import make_http_request


class TestXMLRPCLogging(XmlrpcAPIBaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_request = make_http_request(user=cls.user)

    @patch('tcms.xmlrpc.decorators.create_log', new=XmlRpcLog.objects.create)
    def test_logging_with_authenticated_user(self):
        log_count = XmlRpcLog.objects.filter(user=self.user, method='Env.filter_groups').count()

        env.filter_groups(self.http_request, {})
        new_count = XmlRpcLog.objects.filter(user=self.user, method='Env.filter_groups').count()

        self.assertEqual(new_count, log_count + 1)

    @patch('tcms.xmlrpc.decorators.create_log', new=XmlRpcLog.objects.create)
    def test_logging_with_anonymous_user(self):
        log_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Env.filter_groups').count()

        env.filter_groups(make_http_request(user=AnonymousUser()), {})
        new_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Env.filter_groups').count()

        self.assertEqual(new_count, log_count + 1)
