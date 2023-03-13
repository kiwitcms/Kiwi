#!/usr/bin/env python3

#
# Copyright (c) 2022 Kiwi TCMS project. All rights reserved.
# Author: Alexander Todorov <info@kiwitcms.org>
#

import base64
import ssl
import unittest
from unittest.mock import patch

import requests
from tcms_api import TCMS

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context


class DoNotVerifySSLSession(requests.sessions.Session):
    def get(self, url, **kwargs):
        kwargs.setdefault("verify", False)
        return super().get(url, **kwargs)


class Utf8UploadTestCase(unittest.TestCase):
    @staticmethod
    def upload_files_for_other_tests(rpc):
        with open("tests/ui/data/inline_javascript.svg", "rb") as svg_file:
            b64 = base64.b64encode(svg_file.read()).decode()
            rpc.User.add_attachment("inline_javascript.svg", b64)

    @classmethod
    def setUpClass(cls):
        with patch("requests.sessions.Session") as session:
            session.return_value = DoNotVerifySSLSession()
            cls.rpc = TCMS().exec

        cls.upload_files_for_other_tests(cls.rpc)

    def upload_and_assert(self, filename):
        result = self.rpc.User.add_attachment(filename, "a2l3aXRjbXM=")
        self.assertIn("url", result)
        self.assertIn("filename", result)

    def test_with_filename_in_french(self):
        self.upload_and_assert("Screenshot_20211117-164527_Paramètres.png")

    def test_with_filename_in_bulgarian(self):
        self.upload_and_assert("Screenshot_2021-12-07 Плащане.png")


if __name__ == "__main__":
    unittest.main()
