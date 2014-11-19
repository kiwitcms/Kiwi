# -*- coding: utf-8 -*-
from xmlrpclib import Fault

from django.test import TestCase

from tcms.xmlrpc.filters import wrap_exceptions


class AssertMessage(object):
    SHOULD_BE_400 = "Error code should be 400."
    SHOULD_BE_409 = "Error code should be 409."
    SHOULD_BE_500 = "Error code should be 500."
    SHOULD_BE_403 = "Error code should be 403."
    SHOULD_BE_401 = "Error code should be 401."
    SHOULD_BE_404 = "Error code should be 404."
    SHOULD_BE_501 = "Error code should be 501."
    SHOULD_BE_1 = "Error code should be 1."

    SHOULD_RAISE_EXCEPTION = "Should raise an exception."


class TestFaultCode(TestCase):
    def test_403(self):
        def raise_exception(*args, **kwargs):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied()

        wrapper = wrap_exceptions(raise_exception)

        try:
            wrapper()
        except Fault as f:
            self.assertEqual(f.faultCode, 403, AssertMessage.SHOULD_BE_403)
        else:
            self.fail(AssertMessage.SHOULD_RAISE_EXCEPTION)

    def test_404(self):
        def raise_exception(*args, **kwargs):
            from django.db.models import ObjectDoesNotExist

            raise ObjectDoesNotExist()

        wrapper = wrap_exceptions(raise_exception)

        try:
            wrapper()
        except Fault as f:
            self.assertEqual(f.faultCode, 404, AssertMessage.SHOULD_BE_404)
        else:
            self.fail(AssertMessage.SHOULD_RAISE_EXCEPTION)

    def test_400(self):
        from django.db.models import FieldDoesNotExist
        from django.core.exceptions import FieldError
        from django.core.exceptions import ValidationError
        from django.core.exceptions import MultipleObjectsReturned

        exceptions = [v for k, v in locals().iteritems() if k != 'self']
        exceptions.extend((TypeError, ValueError))

        def raise_exception(cls):
            raise cls()

        wrapper = wrap_exceptions(raise_exception)
        for clazz in exceptions:
            try:
                wrapper(clazz)
            except Fault as f:
                self.assertEqual(f.faultCode, 400, AssertMessage.SHOULD_BE_400)
            else:
                self.fail(AssertMessage.SHOULD_RAISE_EXCEPTION)

    def test_409(self):
        def raise_exception(*args, **kwargs):
            from django.db.utils import IntegrityError

            raise IntegrityError()

        wrapper = wrap_exceptions(raise_exception)

        try:
            wrapper()
        except Fault as f:
            self.assertEqual(f.faultCode, 409, AssertMessage.SHOULD_BE_409)
        else:
            self.fail(AssertMessage.SHOULD_RAISE_EXCEPTION)

    def test_500(self):
        def raise_exception(*args, **kwargs):
            raise Exception()

        wrapper = wrap_exceptions(raise_exception)

        try:
            wrapper()
        except Fault as f:
            self.assertEqual(f.faultCode, 500, AssertMessage.SHOULD_BE_500)
        else:
            self.fail(AssertMessage.SHOULD_RAISE_EXCEPTION)

    def test_501(self):
        def raise_exception(*args, **kwargs):
            raise NotImplementedError()

        wrapper = wrap_exceptions(raise_exception)

        try:
            wrapper()
        except Fault as f:
            self.assertEqual(f.faultCode, 501, AssertMessage.SHOULD_BE_501)
        else:
            self.fail(AssertMessage.SHOULD_RAISE_EXCEPTION)


class TestAutoWrap(TestCase):
    def test_auto_wrap(self):
        from tcms.xmlrpc.api import auth

        func_names = getattr(auth, "__all__")

        for func_name in func_names:
            func = getattr(auth, func_name)
            code = func.func_code
            self.assertEqual(code.co_name, "_decorator")
