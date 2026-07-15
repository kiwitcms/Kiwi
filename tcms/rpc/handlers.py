import html
from datetime import timedelta

from modernrpc.jsonrpc.handler import JsonRpcHandler
from modernrpc.xmlrpc.handler import XmlRpcHandler


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

    def build_success_result(self, request, data):
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
