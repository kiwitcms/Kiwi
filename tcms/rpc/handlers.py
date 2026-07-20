import html
from datetime import timedelta

from modernrpc.exceptions import RPCInvalidRequest
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

    @staticmethod
    def inspect_rpc_args(rpc_request):
        restricted_fields = (
            "password",
            "token",
            "secret",
            "activation_key",
            "api_key",
            "apikey",
        )
        keys_to_check = []
        for arg in rpc_request.args:
            if isinstance(arg, dict):
                keys_to_check.extend(arg.keys())
        kwargs = getattr(rpc_request, "kwargs", None)
        if isinstance(kwargs, dict):
            keys_to_check.extend(kwargs.keys())

        for key in keys_to_check:
            key_str = str(key).lower()
            if any(
                key_str == field or key_str.startswith(f"{field}__")
                for field in restricted_fields
            ):
                raise RPCInvalidRequest("Unsupported field")

    def process_single_request(self, rpc_request, context):
        self.inspect_rpc_args(rpc_request)
        return super().process_single_request(rpc_request, context)

    async def aprocess_single_request(self, rpc_request, context):
        self.inspect_rpc_args(rpc_request)
        return await super().aprocess_single_request(rpc_request, context)

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
