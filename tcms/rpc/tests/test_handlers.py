import html
from datetime import timedelta
from unittest.mock import Mock

from django.test import TestCase
from parameterized import parameterized

from tcms.rpc.handlers import (
    KiwiTCMSHandlerMixin,
    KiwiTCMSJsonRpcHandler,
    KiwiTCMSXmlRpcHandler,
)


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

    def test_tuple_with_html_escape(self):
        data = ("<b>bold</b>", "normal")
        result = self.handler.escape(data)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], html.escape("<b>bold</b>"))
        self.assertEqual(result[1], "normal")

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

    def test_tuple_with_html_escape(self):
        data = ("<b>bold</b>", "normal")
        result = self.handler.escape(data)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], html.escape("<b>bold</b>"))
        self.assertEqual(result[1], "normal")

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


class TestUnicodeNormalization(TestCase):
    def test_nfkc_expands_compatibility_characters(self):
        self.assertEqual(KiwiTCMSHandlerMixin.normalize_text("ﬁ①㎏"), "fi1kg")

    @parameterized.expand(
        [
            (KiwiTCMSJsonRpcHandler.__name__, KiwiTCMSJsonRpcHandler),
            (KiwiTCMSXmlRpcHandler.__name__, KiwiTCMSXmlRpcHandler),
        ]
    )
    def test_fullwidth_markup_is_escaped_after_normalization(
        self, _name, handler_class
    ):
        handler = handler_class()
        result = handler.build_success_result(Mock(), "＜script＞alert(1)＜/script＞")
        self.assertEqual(result.data, "&lt;script&gt;alert(1)&lt;/script&gt;")

    def test_invisible_characters_are_removed(self):
        invisible = (
            "\u00ad\u061c\u115f\u1160\u180e"
            "\u200b\u200c\u200d\u200e\u200f"
            "\u202a\u202b\u202c\u202d\u202e"
            "\u2060\u2061\u2062\u2063\u2064"
            "\u2066\u2067\u2068\u2069"
            "\u3164\ufeff\U000e0041"
        )
        self.assertEqual(KiwiTCMSHandlerMixin.normalize_text(f"a{invisible}b"), "ab")

    def test_control_characters_are_removed(self):
        controls = "".join(
            chr(code)
            for code in (
                *range(0x00, 0x09),
                0x0B,
                0x0C,
                *range(0x0E, 0x20),
                *range(0x7F, 0xA0),
            )
        )
        self.assertEqual(KiwiTCMSHandlerMixin.normalize_text(f"a{controls}b"), "ab")

    def test_whitespace_controls_are_preserved(self):
        self.assertEqual(
            KiwiTCMSHandlerMixin.normalize_text("a\tb\nc\rd"), "a\tb\nc\rd"
        )

    def test_line_separators_become_newlines(self):
        self.assertEqual(
            KiwiTCMSHandlerMixin.normalize_text("a\u2028b\u2029c"), "a\nb\nc"
        )

    def test_nested_values_are_normalized(self):
        data = {"a": ["＜b＞", ("ﬁ",)], "c": timedelta(seconds=1)}
        self.assertEqual(
            KiwiTCMSHandlerMixin.normalize(data),
            {"a": ["<b>", ["fi"]], "c": timedelta(seconds=1)},
        )

    def test_normalization_is_idempotent(self):
        value = "＜①\u200bﬁ"
        self.assertEqual(
            KiwiTCMSHandlerMixin.normalize_text(
                KiwiTCMSHandlerMixin.normalize_text(value)
            ),
            KiwiTCMSHandlerMixin.normalize_text(value),
        )
