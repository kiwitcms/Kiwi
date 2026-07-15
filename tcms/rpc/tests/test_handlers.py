import html
from datetime import timedelta
from unittest.mock import Mock

from django.test import TestCase

from tcms.rpc.handlers import KiwiTCMSJsonRpcHandler, KiwiTCMSXmlRpcHandler


class TestKiwiTCMSJsonRpcHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = KiwiTCMSJsonRpcHandler()
        cls.request = Mock()

    def test_html_escape_in_string(self):
        data = "<script>alert('xss')</script>"
        result = self.handler.build_success_result(self.request, data)
        # build_success_result returns a dict with 'result' key
        self.assertEqual(result.data, html.escape(data))

    def test_timedelta_conversion(self):
        data = timedelta(hours=1, minutes=30)
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data, 5400.0)

    def test_dict_with_html_escape(self):
        data = {"message": "<b>bold</b>", "safe": "normal text"}
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["message"], html.escape("<b>bold</b>"))
        self.assertEqual(result.data["safe"], "normal text")

    def test_dict_with_timedelta(self):
        data = {"duration": timedelta(seconds=90)}
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["duration"], 90.0)

    def test_nested_dict(self):
        data = {"outer": {"inner": "<tag>"}}
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["outer"]["inner"], html.escape("<tag>"))

    def test_list_with_html(self):
        data = ["<p>paragraph</p>", "normal"]
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data[0], html.escape("<p>paragraph</p>"))
        self.assertEqual(result.data[1], "normal")

    def test_list_with_timedelta(self):
        data = [timedelta(minutes=5), timedelta(hours=2)]
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data[0], 300.0)
        self.assertEqual(result.data[1], 7200.0)

    def test_complex_nested_structure(self):
        data = {
            "items": [
                {"name": "<item1>", "time": timedelta(seconds=10)},
                {"name": "<item2>", "time": timedelta(seconds=20)},
            ]
        }
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["items"][0]["name"], html.escape("<item1>"))
        self.assertEqual(result.data["items"][0]["time"], 10.0)
        self.assertEqual(result.data["items"][1]["name"], html.escape("<item2>"))
        self.assertEqual(result.data["items"][1]["time"], 20.0)


class TestKiwiTCMSXmlRpcHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = KiwiTCMSXmlRpcHandler()
        cls.request = Mock()

    def test_html_escape_in_string(self):
        data = "<script>alert('xss')</script>"
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data, html.escape(data))

    def test_timedelta_conversion(self):
        data = timedelta(hours=1, minutes=30)
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data, 5400.0)

    def test_dict_with_html_escape(self):
        data = {"message": "<b>bold</b>", "safe": "normal text"}
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["message"], html.escape("<b>bold</b>"))
        self.assertEqual(result.data["safe"], "normal text")

    def test_dict_with_timedelta(self):
        data = {"duration": timedelta(seconds=90)}
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["duration"], 90.0)

    def test_nested_dict(self):
        data = {"outer": {"inner": "<tag>"}}
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["outer"]["inner"], html.escape("<tag>"))

    def test_list_with_html(self):
        data = ["<p>paragraph</p>", "normal"]
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data[0], html.escape("<p>paragraph</p>"))
        self.assertEqual(result.data[1], "normal")

    def test_list_with_timedelta(self):
        data = [timedelta(minutes=5), timedelta(hours=2)]
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data[0], 300.0)
        self.assertEqual(result.data[1], 7200.0)

    def test_complex_nested_structure(self):
        data = {
            "items": [
                {"name": "<item1>", "time": timedelta(seconds=10)},
                {"name": "<item2>", "time": timedelta(seconds=20)},
            ]
        }
        result = self.handler.build_success_result(self.request, data)
        self.assertEqual(result.data["items"][0]["name"], html.escape("<item1>"))
        self.assertEqual(result.data["items"][0]["time"], 10.0)
        self.assertEqual(result.data["items"][1]["name"], html.escape("<item2>"))
        self.assertEqual(result.data["items"][1]["time"], 20.0)
