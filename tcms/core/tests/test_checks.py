# -*- coding: utf-8 -*-
# pylint: disable=too-many-ancestors
import os
from unittest.mock import patch

from django import test

from tcms.core import checks


class TestInstallationIdCheck(test.TestCase):
    dirs = "/Kiwi/uploads"
    filename = f"{dirs}/installation-id"

    def assert_installation_id(self):
        self.assertTrue(os.path.exists(self.filename))
        with open(self.filename, encoding="utf-8") as file_handle:
            self.assertNotEqual("", file_handle.read().strip())

    def test_when_file_exists_nothing_happens(self):
        with patch("os.path.exists", return_value=True):
            checks.check_installation_id(None)
        self.assert_installation_id()

    def test_when_file_does_not_exist_it_is_created(self):
        os.makedirs(self.dirs, exist_ok=True)

        if os.path.exists(self.filename):
            os.unlink(self.filename)
        self.assertFalse(os.path.exists(self.filename))

        checks.check_installation_id(None)
        self.assert_installation_id()

    def test_when_file_exists_and_is_empty_then_it_is_created(self):
        os.makedirs(self.dirs, exist_ok=True)

        with open(self.filename, "w", encoding="utf-8") as file_handle:
            file_handle.write("")
        self.assertTrue(os.path.exists(self.filename))
        with open(self.filename, encoding="utf-8") as file_handle:
            self.assertEqual("", file_handle.read().strip())

        checks.check_installation_id(None)
        self.assert_installation_id()
