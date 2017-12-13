# -*- coding: utf-8 -*-

import django.contrib.auth

from django.conf import settings
from django.core.exceptions import PermissionDenied

from tcms.xmlrpc.decorators import log_call

__all__ = (
    'login', 'logout', 'login_krbv'
)

__xmlrpc_namespace__ = 'Auth'


@log_call(namespace=__xmlrpc_namespace__)
def login(request, username, password):
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


@log_call(namespace=__xmlrpc_namespace__)
def login_krbv(request):
    """
    .. function:: XML-RPC Auth.login_krbv()

        Login into Kiwi TCMS deployed with Kerberos.

        :return: Session ID
        :rtype: str
    """
    from django.contrib.auth.middleware import RemoteUserMiddleware

    middleware = RemoteUserMiddleware()
    middleware.process_request(request)

    return request.session.session_key


@log_call(namespace=__xmlrpc_namespace__)
def logout(request):
    """
    .. function:: XML-RPC Auth.logout()

        Delete session information

        :return: None
    """
    django.contrib.auth.logout(request)
