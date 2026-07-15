# coding: utf-8
import html
from datetime import timedelta

from modernrpc.handlers import JSONRPCHandler, XMLRPCHandler
from modernrpc.handlers.jsonhandler import JsonSuccessResult
from modernrpc.handlers.xmlhandler import XmlSuccessResult


class KiwiTCMSHandlerMixin:

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
        else:
            return __class__.escape_value(value)
        return value

    def dumps_result(self, result):
        if isinstance(result, (JsonSuccessResult, XmlSuccessResult)):
            result.data = __class__.escape(result.data)
        return super().dumps_result(result)


class KiwiTCMSJsonRpcHandler(
    KiwiTCMSHandlerMixin, JSONRPCHandler
):  # pylint: disable=remove-empty-class
    pass


class KiwiTCMSXmlRpcHandler(
    KiwiTCMSHandlerMixin, XMLRPCHandler
):  # pylint: disable=remove-empty-class
    pass
