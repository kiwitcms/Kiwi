# -*- coding: utf-8 -*-

import django.contrib.auth
from django.core.exceptions import PermissionDenied
from modernrpc.core import REQUEST_KEY, rpc_method

__all__ = (
    "login",
    "logout",
)


@rpc_method(name="Auth.login")
def login(
    username, password, **kwargs
):  # pylint: disable=missing-api-permissions-required
    """
    .. function:: RPC Auth.login(username, password)

        Login into Kiwi TCMS.

        :param username: A Kiwi TCMS login
        :type username: str
        :param password: The password
        :type password: str
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Session ID
        :rtype: str
        :raises PermissionDenied: if username or password doesn't match or missing
    """
    # Get the current request
    request = kwargs.get(REQUEST_KEY)

    if not username or not password:
        raise PermissionDenied("Username and password is required")

    user = django.contrib.auth.authenticate(
        request, username=username, password=password
    )
    if user is not None:
        django.contrib.auth.login(request, user)
        return request.session.session_key

    raise PermissionDenied("Wrong username or password")


@rpc_method(name="Auth.logout")
def logout(**kwargs):  # pylint: disable=missing-api-permissions-required
    """
    .. function:: RPC Auth.logout()

        Delete session information
    """
    # Get the current request
    request = kwargs.get(REQUEST_KEY)
    django.contrib.auth.logout(request)
