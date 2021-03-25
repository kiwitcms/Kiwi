# -*- coding: utf-8 -*-

from modernrpc.auth.basic import http_basic_auth_login_required
from modernrpc.core import rpc_method

from tcms import __version__

__all__ = ("version",)


@http_basic_auth_login_required
@rpc_method(name="KiwiTCMS.version")
def version():
    """
    .. function:: RPC KiwiTCMS.version()

        :return: Current version of Kiwi TCMS installation.
        :rtype: string
    """
    return __version__
