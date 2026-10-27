import html
import re
import unicodedata
from datetime import timedelta

from modernrpc.exceptions import RPCInvalidRequest
from modernrpc.jsonrpc.handler import JsonRpcHandler
from modernrpc.xmlrpc.handler import XmlRpcHandler

# Control characters (Unicode category Cc) which have no place in an RPC
# response. TAB, LF and CR are kept because they are meaningful whitespace.
_CONTROL_CHARS = re.compile(
    "["
    "\x00-\x08"  # NULL through BACKSPACE
    "\x0b"  # LINE TABULATION
    "\x0c"  # FORM FEED
    "\x0e-\x1f"  # SHIFT OUT through UNIT SEPARATOR
    "\x7f"  # DELETE
    "\x80-\x9f"  # C1 controls
    "]"
)

# Invisible formatting characters (category Cf) and fillers which can hide
# content from humans, break tokenisation or reorder the displayed text.
_INVISIBLE_CHARS = re.compile(
    "["
    "\u00ad"  # SOFT HYPHEN
    "\u061c"  # ARABIC LETTER MARK
    "\u115f\u1160"  # HANGUL CHOSEONG/JUNGSEONG FILLER
    "\u180e"  # MONGOLIAN VOWEL SEPARATOR
    "\u200b-\u200f"  # ZWSP, ZWNJ, ZWJ, LRM, RLM
    "\u202a-\u202e"  # bidi embeddings and overrides
    "\u2060-\u2064"  # word joiner and invisible operators
    "\u2066-\u2069"  # bidi isolates
    "\u3164"  # HANGUL FILLER
    "\ufeff"  # BOM / ZWNBSP
    "\U000e0000-\U000e007f"  # deprecated tag characters
    "]"
)

# Unicode line and paragraph separators. Some parsers treat them as line
# breaks, so normalise them to a plain newline.
_LINE_SEPARATORS = re.compile(
    "["
    "\u2028"  # LINE SEPARATOR
    "\u2029"  # PARAGRAPH SEPARATOR
    "]"
)


class KiwiTCMSHandlerMixin:

    @staticmethod
    def normalize_text(value):
        value = unicodedata.normalize("NFKC", value)
        value = _LINE_SEPARATORS.sub("\n", value)
        value = _INVISIBLE_CHARS.sub("", value)
        value = _CONTROL_CHARS.sub("", value)
        return value

    @staticmethod
    def normalize(value):
        if isinstance(value, dict):
            return {key: __class__.normalize(val) for key, val in value.items()}
        if isinstance(value, (list, tuple)):
            result = []
            for item in value:
                result.append(__class__.normalize(item))
            return result
        if isinstance(value, str):
            return __class__.normalize_text(value)
        return value

    @staticmethod
    def escape_value(value):
        if isinstance(value, str):
            return html.escape(value)
        if isinstance(value, timedelta):
            return value.total_seconds()
        return value

    @staticmethod
    def escape(value):
        """Recursively walk *value* and transform it in place."""
        if isinstance(value, dict):
            for key, val in value.items():
                value[key] = __class__.escape(val)
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                value[idx] = __class__.escape(item)
        elif isinstance(value, tuple):
            return tuple(__class__.escape(item) for item in value)
        else:
            return __class__.escape_value(value)
        return value

    @staticmethod
    def dict_keys(extract_from, depth=0):
        if depth > 4:
            return

        if isinstance(extract_from, dict):
            for key, value in extract_from.items():
                yield key
                yield from __class__.dict_keys(value, depth + 1)
        elif isinstance(extract_from, (list, tuple)):
            for value in extract_from:
                yield from __class__.dict_keys(value, depth + 1)

    @staticmethod
    def inspect_rpc_args(rpc_request):
        if rpc_request.method_name.endswith(
            ".create"
        ) or rpc_request.method_name.endswith(".update"):
            return

        restricted_fields = (
            "__email__",
            "activation_key",
            "api_key",
            "apikey",
            "password",
            "secret",
            "token",
        )

        keys_to_check = list(__class__.dict_keys(rpc_request.args))
        keys_to_check.extend(__class__.dict_keys(getattr(rpc_request, "kwargs", None)))

        for key in keys_to_check:
            key_str = str(key).lower()
            if any(key_str.find(field) > -1 for field in restricted_fields):
                raise RPCInvalidRequest("Unsupported field")

    def process_single_request(self, rpc_request, context):
        try:
            self.inspect_rpc_args(rpc_request)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            rpc_exc = context.server.on_error(exc, context)
            return self.build_error_result(
                request=rpc_request,
                code=rpc_exc.code,
                message=rpc_exc.message,
                data=rpc_exc.data,
            )

        return super().process_single_request(rpc_request, context)

    async def aprocess_single_request(self, rpc_request, context):
        try:
            self.inspect_rpc_args(rpc_request)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            rpc_exc = context.server.on_error(exc, context)
            return self.build_error_result(
                request=rpc_request,
                code=rpc_exc.code,
                message=rpc_exc.message,
                data=rpc_exc.data,
            )

        return await super().aprocess_single_request(rpc_request, context)

    def build_success_result(self, request, data):
        data = __class__.normalize(data)
        data = __class__.escape(data)
        return super().build_success_result(request, data)


class KiwiTCMSJsonRpcHandler(
    KiwiTCMSHandlerMixin, JsonRpcHandler
):  # pylint: disable=remove-empty-class
    pass


class KiwiTCMSXmlRpcHandler(
    KiwiTCMSHandlerMixin, XmlRpcHandler
):  # pylint: disable=remove-empty-class
    pass
