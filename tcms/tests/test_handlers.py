import html
from unittest import TestCase
from unittest.mock import patch

from django.test import RequestFactory

from tcms.handlers import SafeJSONRPCHandler


class TestSafeJSONRPCHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_exec_procedure = "modernrpc.handlers.JSONRPCHandler.execute_procedure"
        cls.rpc_handler = SafeJSONRPCHandler(RequestFactory(), entry_point="/json-rpc/")

    def test_html_escape(self):
        payload = "<html></html>"
        with patch(self.base_exec_procedure, return_value=payload):
            self.assertEqual(
                self.rpc_handler.execute_procedure("method_name"), html.escape(payload)
            )

    def test_dict_escape(self):
        with patch(self.base_exec_procedure, return_value={"html": "<html></html>"}):
            self.assertDictEqual(
                self.rpc_handler.execute_procedure("method_name"),
                {"html": html.escape("<html></html>")},
            )

    def test_list_escape(self):
        with patch(self.base_exec_procedure, return_value=["<html></html>"]):
            self.assertListEqual(
                self.rpc_handler.execute_procedure("method_name"),
                [html.escape("<html></html>")],
            )

        with patch(self.base_exec_procedure, return_value=[{"html": "<html></html>"}]):
            self.assertListEqual(
                self.rpc_handler.execute_procedure("method_name"),
                [{"html": html.escape("<html></html>")}],
            )
