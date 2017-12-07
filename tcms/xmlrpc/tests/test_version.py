# -*- coding: utf-8 -*-
from mock import patch
from django.test import TestCase
from django.contrib.auth.models import AnonymousUser

from tcms.xmlrpc.api import version
from tcms.xmlrpc import XMLRPC_VERSION
from tcms.xmlrpc.models import XmlRpcLog

from tcms.tests.factories import UserFactory
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest
from tcms.xmlrpc.tests.utils import make_http_request


class TestVersion(TestCase):
    def test_get_version(self):
        response = version.get(None)
        self.assertEqual(response, XMLRPC_VERSION)


class TestXMLRPCLogging(XmlrpcAPIBaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.http_request = make_http_request(user=cls.user)

    @patch('tcms.xmlrpc.decorators.create_log', new=XmlRpcLog.objects.create)
    def test_logging_with_authenticated_user(self):
        log_count = XmlRpcLog.objects.filter(user=self.user, method='Version.get').count()

        version.get(self.http_request)
        new_count = XmlRpcLog.objects.filter(user=self.user, method='Version.get').count()

        self.assertEqual(new_count, log_count + 1)

    @patch('tcms.xmlrpc.decorators.create_log', new=XmlRpcLog.objects.create)
    def test_logging_with_anonymous_user(self):
        log_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Version.get').count()

        version.get(make_http_request(user=AnonymousUser()))
        new_count = XmlRpcLog.objects.filter(user__username='Anonymous',
                                             method='Version.get').count()

        self.assertEqual(new_count, log_count + 1)
