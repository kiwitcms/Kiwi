# -*- coding: utf-8 -*-

import six
from six.moves import http_client

from django.test import TestCase

from tcms.xmlrpc.filters import wrap_exceptions
from tcms.xmlrpc.tests.utils import XmlrpcAPIBaseTest


class TestFaultCode(XmlrpcAPIBaseTest):

    def test_403(self):
        def raise_exception(*args, **kwargs):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied()

        wrapper = wrap_exceptions(raise_exception)
        self.assertRaisesXmlrpcFault(http_client.FORBIDDEN, wrapper)

    def test_404(self):
        def raise_exception(*args, **kwargs):
            from django.db.models import ObjectDoesNotExist
            raise ObjectDoesNotExist()

        wrapper = wrap_exceptions(raise_exception)
        self.assertRaisesXmlrpcFault(http_client.NOT_FOUND, wrapper)

    def test_400(self):
        exceptions = [v for k, v in six.iteritems(locals().copy()) if k != 'self']
        exceptions.extend((TypeError, ValueError))

        def raise_exception(cls):
            raise cls()

        wrapper = wrap_exceptions(raise_exception)
        for clazz in exceptions:
            self.assertRaisesXmlrpcFault(http_client.BAD_REQUEST, wrapper, clazz)

    def test_409(self):
        def raise_exception(*args, **kwargs):
            from django.db.utils import IntegrityError
            raise IntegrityError()

        wrapper = wrap_exceptions(raise_exception)
        self.assertRaisesXmlrpcFault(http_client.CONFLICT, wrapper)

    def test_500(self):
        def raise_exception(*args, **kwargs):
            raise Exception()

        wrapper = wrap_exceptions(raise_exception)
        self.assertRaisesXmlrpcFault(http_client.INTERNAL_SERVER_ERROR, wrapper)

    def test_501(self):
        def raise_exception(*args, **kwargs):
            raise NotImplementedError()

        wrapper = wrap_exceptions(raise_exception)
        self.assertRaisesXmlrpcFault(http_client.NOT_IMPLEMENTED, wrapper)


class TestAutoWrap(TestCase):
    def test_auto_wrap(self):
        from tcms.xmlrpc.api import auth

        func_names = getattr(auth, "__all__")

        for func_name in func_names:
            func = getattr(auth, func_name)
            code = six.get_function_code(func)
            self.assertEqual(code.co_name, "_decorator")
