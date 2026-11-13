# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>

# Licensed under the GPL 2.0 or later: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from modernrpc.constants import Protocol
from modernrpc.exceptions import RPCInvalidParams
from modernrpc.server import RpcServer

from tcms.rpc import registry


def type_error_as_invalid_params(exception, _context):
    if isinstance(exception, TypeError):
        raise RPCInvalidParams(str(exception)) from exception


xml_rpc_server = RpcServer(
    supported_protocol=Protocol.XML_RPC, error_handler=type_error_as_invalid_params
)
json_rpc_server = RpcServer(
    supported_protocol=Protocol.JSON_RPC, error_handler=type_error_as_invalid_params
)


def rpc_method(name, auth, context_target=None):
    def decorator(func):  # pylint: disable=nested-function-found
        json_rpc_server.register_procedure(
            func, name=name, auth=auth, context_target=context_target
        )
        xml_rpc_server.register_procedure(
            func, name=name, auth=auth, context_target=context_target
        )
        registry.register(func, name=name, auth=auth, context_target=context_target)
        return func

    return decorator
