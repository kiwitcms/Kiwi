# -*- coding: utf-8 -*-

import django.contrib.auth
from django.core.exceptions import PermissionDenied
from django.contrib.auth.middleware import RemoteUserMiddleware
from modernrpc.core import REQUEST_KEY, rpc_method

__all__ = (
    'login',
    'login_krbv',
    'logout',
)


@rpc_method(name='Auth.login')
def login(username, password, **kwargs):
    """
    .. function:: XML-RPC Auth.login(username, password)

        Login into Kiwi TCMS.

        :param username: A Kiwi TCMS login or email address
        :type username: str
        :param password: The password
        :type password: str
        :return: Session ID
        :rtype: str
        :raises PermissionDenied: if username or password doesn't match or missing
    """
    # Get the current request
    request = kwargs.get(REQUEST_KEY)

    if not username or not password:
        raise PermissionDenied('Username and password is required')

    user = django.contrib.auth.authenticate(request, username=username, password=password)
    if user is not None:
        django.contrib.auth.login(request, user)
        return request.session.session_key

    raise PermissionDenied('Wrong username or password')


@rpc_method(name='Auth.login_krbv')
def login_krbv(**kwargs):
    """
    .. function:: XML-RPC Auth.login_krbv()

        Login into Kiwi TCMS deployed with Kerberos.

        :return: Session ID
        :rtype: str
    """

    # Get the current request
    request = kwargs.get(REQUEST_KEY)

    middleware = RemoteUserMiddleware()
    middleware.process_request(request)

    return request.session.session_key


@rpc_method(name='Auth.logout')
def logout(**kwargs):
    """
    .. function:: XML-RPC Auth.logout()

        Delete session information

        :return: None
    """
    # Get the current request
    request = kwargs.get(REQUEST_KEY)
    django.contrib.auth.logout(request)
