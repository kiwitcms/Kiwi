import django.contrib.auth
from django.core.exceptions import PermissionDenied

from tcms.rpc.views import rpc_method


@rpc_method(
    name="Auth.login",
    auth=None,
    context_target="rpc_context",
)
def login(
    username, password, rpc_context=None
):  # pylint: disable=missing-api-permissions-required
    """
    .. function:: RPC Auth.login(username, password)

        Login into Kiwi TCMS.

        :param username: A Kiwi TCMS login
        :type username: str
        :param password: The password
        :type password: str
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Session ID
        :rtype: str
        :raises PermissionDenied: if username or password doesn't match or missing
    """
    # Get the current request
    request = rpc_context.request

    if not username or not password:
        raise PermissionDenied("Username and password is required")

    user = django.contrib.auth.authenticate(
        request, username=username, password=password
    )
    if user is not None:
        django.contrib.auth.login(request, user)
        return request.session.session_key

    raise PermissionDenied("Wrong username or password")


@rpc_method(
    name="Auth.logout",
    auth=None,
    context_target="rpc_context",
)
def logout(rpc_context=None):  # pylint: disable=missing-api-permissions-required
    """
    .. function:: RPC Auth.logout()

        Delete session information
    """
    # Get the current request
    request = rpc_context.request
    django.contrib.auth.logout(request)
