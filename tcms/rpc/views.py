# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from modernrpc.constants import Protocol
from modernrpc.server import RpcServer

xml_rpc_server = RpcServer(supported_protocol=Protocol.XML_RPC)
json_rpc_server = RpcServer(supported_protocol=Protocol.JSON_RPC)


def rpc_method(name, auth, context_target=None):
    def decorator(func):  # pylint: disable=nested-function-found
        json_rpc_server.register_procedure(
            func, name=name, auth=auth, context_target=context_target
        )
        xml_rpc_server.register_procedure(
            func, name=name, auth=auth, context_target=context_target
        )
        return func

    return decorator
