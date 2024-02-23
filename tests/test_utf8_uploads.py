#!/usr/bin/env python3

#
# Copyright (c) 2022-2024 Kiwi TCMS project. All rights reserved.
# Author: Alexander Todorov <info@kiwitcms.org>
#

import base64
import os
import ssl
import sys
import tempfile
import unittest
from unittest.mock import patch
from xmlrpc.client import Fault as XmlRPCFault

import requests
from tcms_api import TCMS

tcms_root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(tcms_root_path)

from tcms.settings.common import FILE_UPLOAD_MAX_SIZE

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
    def create_file(size, name):
        """
        Create a temporary file with specific size.
        """
        (_handle, file_name) = tempfile.mkstemp(prefix=f"kiwitcms-test-{name}.")
        with open(file_name, "wb") as file:
            for _ in range(size):
                file.write(b"T")

        return file_name

    def b64_file(self, size, name):
        """
        Create a temporary file and return it's contents in Base64,
        which can be passed directly to rpc.User.add_attachment().
        """
        file_name = self.create_file(size, name)
        with open(file_name, "rb") as file_handle:
            file_content = file_handle.read()
            file_content = base64.b64encode(file_content).decode()
            return (file_name, file_content)

    @classmethod
    def setUpClass(cls):
        with patch("requests.sessions.Session") as session:
            session.return_value = DoNotVerifySSLSession()
            cls.rpc = TCMS().exec

    def upload_and_assert(self, filename, contents="a2l3aXRjbXM="):
        result = self.rpc.User.add_attachment(filename, contents)
        self.assertIn("url", result)
        self.assertIn("filename", result)

    def test_with_filename_in_french(self):
        self.upload_and_assert("Screenshot_20211117-164527_Paramètres.png")

    def test_with_filename_in_bulgarian(self):
        self.upload_and_assert("Screenshot_2021-12-07 Плащане.png")

    def test_uploading_file_with_maximum_allowed_size_should_work(self):
        file_name, file_content = self.b64_file(FILE_UPLOAD_MAX_SIZE, "5mb-file")
        self.upload_and_assert(file_name, file_content)

    def test_uploading_file_with_size_greater_than_maximum_should_fail(self):
        file_name, file_content = self.b64_file(FILE_UPLOAD_MAX_SIZE + 1, "file-gt-5mb")
        with self.assertRaisesRegex(XmlRPCFault, "File exceeds maximum size"):
            self.rpc.User.add_attachment(file_name, file_content)


if __name__ == "__main__":
    unittest.main()
