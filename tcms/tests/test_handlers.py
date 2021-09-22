import html
from datetime import timedelta
from unittest import TestCase
from unittest.mock import patch

from django.test import RequestFactory

from tcms.handlers import KiwiTCMSJsonRpcHandler, KiwiTCMSXmlRpcHandler


class TestKiwiTCMSJsonRpcHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_exec_procedure = "modernrpc.handlers.JSONRPCHandler.execute_procedure"
        cls.rpc_handler = KiwiTCMSJsonRpcHandler(
            RequestFactory(), entry_point="/json-rpc/"
        )

    def test_html_escape(self):
        payload = "<html></html>"
        with patch(self.base_exec_procedure, return_value=payload):
            self.assertEqual(
                self.rpc_handler.execute_procedure("method_name"), html.escape(payload)
            )

    def test_timedelta_to_seconds(self):
        with patch(self.base_exec_procedure, return_value=timedelta(hours=1)):
            self.assertEqual(self.rpc_handler.execute_procedure("method_name"), 3600.0)

    def test_dict_escape(self):
        with patch(self.base_exec_procedure, return_value={"html": "<html></html>"}):
            self.assertDictEqual(
                self.rpc_handler.execute_procedure("method_name"),
                {"html": html.escape("<html></html>")},
            )

    def test_dict_with_timedelta(self):
        with patch(
            self.base_exec_procedure, return_value={"duration": timedelta(hours=1)}
        ):
            self.assertDictEqual(
                self.rpc_handler.execute_procedure("method_name"),
                {"duration": 3600.0},
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

    def test_list_with_timedelta(self):
        with patch(self.base_exec_procedure, return_value=[timedelta(hours=1)]):
            self.assertListEqual(
                self.rpc_handler.execute_procedure("method_name"),
                [3600.0],
            )

        with patch(
            self.base_exec_procedure, return_value=[{"duration": timedelta(hours=1)}]
        ):
            self.assertListEqual(
                self.rpc_handler.execute_procedure("method_name"),
                [{"duration": 3600.0}],
            )


class TestKiwiTCMSXmlRpcHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_exec_procedure = "modernrpc.handlers.XMLRPCHandler.execute_procedure"
        cls.rpc_handler = KiwiTCMSXmlRpcHandler(
            RequestFactory(), entry_point="/xml-rpc/"
        )

    def test_timedelta_to_seconds(self):
        with patch(self.base_exec_procedure, return_value=timedelta(hours=1)):
            self.assertEqual(self.rpc_handler.execute_procedure("method_name"), 3600.0)

    def test_dict_with_timedelta(self):
        with patch(
            self.base_exec_procedure, return_value={"duration": timedelta(hours=1)}
        ):
            self.assertDictEqual(
                self.rpc_handler.execute_procedure("method_name"),
                {"duration": 3600.0},
            )

    def test_list_with_timedelta(self):
        with patch(self.base_exec_procedure, return_value=[timedelta(hours=1)]):
            self.assertListEqual(
                self.rpc_handler.execute_procedure("method_name"),
                [3600.0],
            )

        with patch(
            self.base_exec_procedure, return_value=[{"duration": timedelta(hours=1)}]
        ):
            self.assertListEqual(
                self.rpc_handler.execute_procedure("method_name"),
                [{"duration": 3600.0}],
            )
