# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

from http import HTTPStatus

from django import test
from django.http import HttpResponseForbidden

from tcms.utils import github


class CalculateSignatureTestCase(test.TestCase):
    def test_return_format(self):
        self.assertEqual(
            github.calculate_signature(b"secret", b"content"),
            "sha1=0bd98d1a7514a85bbb8377bb8d750b6e01494056",
        )


class VerifySignatureTestCase(test.TestCase):
    def setUp(self):
        self.factory = test.RequestFactory()
        self.url = "/"

    def test_missing_signature_header(self):
        request = self.factory.post(self.url)
        result = github.verify_signature(request, b"")

        self.assertIsInstance(result, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, result.status_code)

    def test_invalid_signature_header(self):
        request = self.factory.post(self.url)
        request.META["HTTP_X_HUB_SIGNATURE"] = "invalid-ssh1"
        result = github.verify_signature(request, b"")

        self.assertIsInstance(result, HttpResponseForbidden)
        self.assertEqual(HTTPStatus.FORBIDDEN, result.status_code)

    def test_valid_signature_header(self):
        request = self.factory.post(self.url)
        request.META["HTTP_X_HUB_SIGNATURE"] = github.calculate_signature(
            b"secret", request.body
        )
        result = github.verify_signature(request, b"secret")
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
