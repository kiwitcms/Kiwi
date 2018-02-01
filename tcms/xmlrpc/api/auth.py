# -*- coding: utf-8 -*-

import django.contrib.auth

from django.conf import settings
from modernrpc.core import rpc_method
from modernrpc.core import REQUEST_KEY
from django.core.exceptions import PermissionDenied

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
    from tcms.core.contrib.auth import get_backend

    user = None
    # Get the current request
    request = kwargs.get(REQUEST_KEY)

    if not username or not password:
        raise PermissionDenied('Username and password is required')

    for backend_str in settings.AUTHENTICATION_BACKENDS:
        backend = get_backend(backend_str)
        user = backend.authenticate(request, username, password)

        if user:
            user.backend = "%s.%s" % (backend.__module__,
                                      backend.__class__.__name__)
            django.contrib.auth.login(request, user)
            return request.session.session_key

    if user is None:
        raise PermissionDenied('Wrong username or password')


@rpc_method(name='Auth.login_krbv')
def login_krbv(**kwargs):
    """
    .. function:: XML-RPC Auth.login_krbv()

        Login into Kiwi TCMS deployed with Kerberos.

        :return: Session ID
        :rtype: str
    """
    from django.contrib.auth.middleware import RemoteUserMiddleware

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
