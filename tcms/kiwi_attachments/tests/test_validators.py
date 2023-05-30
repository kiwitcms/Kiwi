# -*- coding: utf-8 -*-
# pylint: disable=attribute-defined-outside-init, invalid-name, objects-update-used

import base64
from xmlrpc.client import Fault

from django.utils.translation import gettext_lazy as _
from parameterized import parameterized

from tcms.rpc.tests.utils import APITestCase


class TestValidators(APITestCase):
    @parameterized.expand(
        [
            "inline_javascript.svg",
            "inline_javascript_mixed_case.svg",
        ]
    )
    def test_uploading_svg_with_inline_script_should_fail(self, file_name):
        with open(f"tests/ui/data/{file_name}", "rb") as svg_file:
            b64 = base64.b64encode(svg_file.read()).decode()

            tag_name = "script"
            message = str(_(f"File contains forbidden tag: <{tag_name}>"))
            with self.assertRaisesRegex(Fault, message):
                self.rpc_client.User.add_attachment("inline_javascript.svg", b64)

    @parameterized.expand(
        [
            "svg_with_onload_attribute.svg",
        ]
    )
    def test_uploading_svg_with_forbidden_attributes_should_fail(self, file_name):
        with open(f"tests/ui/data/{file_name}", "rb") as svg_file:
            b64 = base64.b64encode(svg_file.read()).decode()

            attr_name = "onload"
            message = str(_(f"File contains forbidden attribute: `{attr_name}`"))
            with self.assertRaisesRegex(Fault, message):
                self.rpc_client.User.add_attachment("image.svg", b64)

    def test_uploading_filename_ending_in_dot_exe_should_fail(self):
        message = str(_("Uploading executable files is forbidden"))
        with self.assertRaisesRegex(Fault, message):
            self.rpc_client.User.add_attachment("hello.exe", "a2l3aXRjbXM=")

    def test_uploading_real_exe_file_should_fail(self):
        with open("tests/ui/data/reactos_csrss.exe", "rb") as exe_file:
            b64 = base64.b64encode(exe_file.read()).decode()

            message = str(_("Uploading executable files is forbidden"))
            with self.assertRaisesRegex(Fault, message):
                self.rpc_client.User.add_attachment("csrss.exe_from_reactos", b64)
