#!/usr/bin/env python3

#
# Copyright (c) 2022 Kiwi TCMS project. All rights reserved.
# Author: Alexander Todorov <info@kiwitcms.org>
#

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
    @classmethod
    def setUpClass(cls):
        with patch("requests.sessions.Session") as session:
            session.return_value = DoNotVerifySSLSession()
            cls.rpc = TCMS().exec

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
