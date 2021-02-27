# Copyright (c) 2021 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

import astroid


def is_api_function(node):
    # API functions always have @rpc_method decorator
    if not node.decorators:
        return False

    for decorator in node.decorators.nodes:
        if (
            isinstance(decorator, astroid.Call)
            and isinstance(decorator.func, astroid.Name)
            and decorator.func.name == "rpc_method"
        ):
            return True

    return False
