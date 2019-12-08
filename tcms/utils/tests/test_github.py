# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

from http import HTTPStatus

from django import test
from django.http import HttpResponseForbidden

from tcms.utils import github


class VerifySignatureTestCase(test.TestCase):
    def setUp(self):
        self.factory = test.RequestFactory()
        self.url = '/'

    def test_missing_signature_header(self):
        request = self.factory.post(self.url)
        result = github.verify_signature(request, b'')

        self.assertIsInstance(result, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, result.status_code)

    def test_invalid_signature_header(self):
        request = self.factory.post(self.url)
        request.META['HTTP_X_HUB_SIGNATURE'] = 'invalid-ssh1'
        result = github.verify_signature(request, b'')

        self.assertIsInstance(result, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, result.status_code)
