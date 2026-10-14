# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from dataclasses import dataclass


@dataclass
class RpcMethod:
    func: object
    name: str
    auth: object
    context_target: str | None = None


REGISTRY: "dict[str, RpcMethod]" = {}


def register(func, name, auth, context_target=None):
    REGISTRY[name] = RpcMethod(
        func=func,
        name=name,
        auth=auth,
        context_target=context_target,
    )
