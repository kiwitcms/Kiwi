import html
from datetime import timedelta
from unittest import TestCase

from modernrpc.handlers.jsonhandler import JsonSuccessResult
from modernrpc.handlers.xmlhandler import XmlSuccessResult

from tcms.handlers import KiwiTCMSJsonRpcHandler, KiwiTCMSXmlRpcHandler


class TestKiwiTCMSJsonRpcHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_result = JsonSuccessResult(None)
        cls.base_result.set_jsonrpc_data(
            request_id=1, version="2.0", is_notification=False
        )
        cls.rpc_handler = KiwiTCMSJsonRpcHandler(entry_point="/json-rpc/")

    def test_html_escape(self):
        payload = "<html></html>"
        self.base_result.data = payload
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": "%s"}' % html.escape(payload),
        )

    def test_timedelta_to_seconds(self):
        self.base_result.data = timedelta(hours=1)
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": 3600.0}',
        )

    def test_dict_escape(self):
        self.base_result.data = {"html": "<html></html>"}
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": {"html": "%s"}}'
            % html.escape("<html></html>"),
        )

    def test_dict_with_timedelta(self):
        self.base_result.data = {"duration": timedelta(hours=1)}
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": {"duration": 3600.0}}',
        )

    def test_list_escape(self):
        self.base_result.data = ["<html></html>"]
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": ["%s"]}'
            % html.escape("<html></html>"),
        )
        self.base_result.data = [{"html": "<html></html>"}]
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": [{"html": "%s"}]}'
            % html.escape("<html></html>"),
        )

    def test_list_with_timedelta(self):
        self.base_result.data = [timedelta(hours=1)]
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": [3600.0]}',
        )

        self.base_result.data = [{"duration": timedelta(hours=1)}]
        self.assertEqual(
            self.rpc_handler.dumps_result(self.base_result),
            '{"id": 1, "jsonrpc": "2.0", "result": [{"duration": 3600.0}]}',
        )


class TestKiwiTCMSXmlRpcHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rpc_handler = KiwiTCMSXmlRpcHandler(entry_point="/xml-rpc/")

    def test_timedelta_to_seconds(self):
        result = XmlSuccessResult(data=timedelta(hours=1))
        self.assertIn(
            "<param>\n<value><double>3600.0</double></value>\n</param>",
            self.rpc_handler.dumps_result(result),
        )

    def test_dict_with_timedelta(self):
        result = XmlSuccessResult(data={"duration": timedelta(hours=1)})
        self.assertIn(
            "<param>\n<value><struct>\n<member>\n<name>duration</name>\n"
            "<value><double>3600.0</double></value>\n"
            "</member>\n</struct></value>\n</param>",
            self.rpc_handler.dumps_result(result),
        )

    def test_list_with_timedelta(self):
        result = XmlSuccessResult(data=[timedelta(hours=1)])
        self.assertIn(
            "<params>\n<param>\n<value><array><data>\n"
            "<value><double>3600.0</double></value>\n"
            "</data></array></value>\n</param>",
            self.rpc_handler.dumps_result(result),
        )

        result = XmlSuccessResult(data=[{"duration": timedelta(hours=1)}])
        self.assertIn(
            "<param>\n<value><array><data>\n<value><struct>\n<member>\n<name>duration</name>\n"
            "<value><double>3600.0</double></value>\n</member>\n</struct></value>\n"
            "</data></array></value>\n</param>",
            self.rpc_handler.dumps_result(result),
        )
