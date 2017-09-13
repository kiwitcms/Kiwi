# -*- coding: utf-8 -*-

import django.contrib.auth

from django.conf import settings
from django.core.exceptions import PermissionDenied

from tcms.xmlrpc.decorators import log_call

__all__ = (
    'login', 'logout', 'login_krbv'
)

__xmlrpc_namespace__ = 'Auth'


def check_user_name(parameters):
    username = parameters.get('username')
    password = parameters.get('password')
    if not username or not password:
        raise PermissionDenied('Username and password is required')

    return username, password


@log_call(namespace=__xmlrpc_namespace__)
def login(request, parameters):
    """
    Description: Login into Kiwi TCMS
    Params:      $parameters - Hash: keys must match valid search fields.
    +-------------------------------------------------------------------+
    |                    Login Parameters                               |
    +-------------------------------------------------------------------+
    |        Key          |          Valid Values                       |
    | username            | A Kiwi TCMS login (email address)         |
    | password            | String                                      |
    +-------------------------------------------------------------------+

    Returns:     String: Session ID.

    Example:
    >>> Auth.login({'username': 'foo', 'password': 'bar'})
    """
    from tcms.core.contrib.auth import get_backend

    user = None

    for backend_str in settings.AUTHENTICATION_BACKENDS:
        backend = get_backend(backend_str)
        user = backend.authenticate(*check_user_name(parameters))

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
    Description: Login into Kiwi TCMS deployed with mod_auth_kerb

    Returns:     String: Session ID.

    Example:
    $ kinit
    Password for username@example.com:

    $ python
    >>> Auth.login_krbv()
    """
    from django.contrib.auth.middleware import RemoteUserMiddleware

    middleware = RemoteUserMiddleware()
    middleware.process_request(request)

    return request.session.session_key


@log_call(namespace=__xmlrpc_namespace__)
def logout(request):
    """Description: Delete session information."""
    django.contrib.auth.logout(request)
    return
