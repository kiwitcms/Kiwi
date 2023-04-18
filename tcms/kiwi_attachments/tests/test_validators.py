# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used

import base64
from xmlrpc.client import Fault

from tcms.rpc.tests.utils import APITestCase


class TestValidators(APITestCase):
    def test_uploading_svg_with_inline_script_should_fail(self):
        with open("tests/ui/data/inline_javascript.svg", "rb") as svg_file:
            b64 = base64.b64encode(svg_file.read()).decode()

            with self.assertRaisesRegex(Fault, "File contains forbidden <script> tag"):
                self.rpc_client.User.add_attachment("inline_javascript.svg", b64)

    def test_uploading_filename_ending_in_dot_exe_should_fail(self):
        with self.assertRaisesRegex(Fault, "Uploading executable files is forbidden"):
            self.rpc_client.User.add_attachment("hello.exe", "a2l3aXRjbXM=")

    def test_uploading_real_exe_file_should_fail(self):
        with open("tests/ui/data/reactos_csrss.exe", "rb") as exe_file:
            b64 = base64.b64encode(exe_file.read()).decode()

            with self.assertRaisesRegex(
                Fault, "Uploading executable files is forbidden"
            ):
                self.rpc_client.User.add_attachment("csrss.exe_from_reactos", b64)
