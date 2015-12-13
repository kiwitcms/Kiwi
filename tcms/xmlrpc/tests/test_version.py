# -*- coding: utf-8 -*-
from django.test import TestCase


class TestVersion(TestCase):

    def test_get_version(self):
        from tcms.xmlrpc import XMLRPC_VERSION
        from tcms.xmlrpc.api import version

        response = version.get(None)
        self.assertEqual(response, XMLRPC_VERSION)
