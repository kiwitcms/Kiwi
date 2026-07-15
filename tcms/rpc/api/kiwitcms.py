from tcms import __version__
from tcms.rpc.decorators import django_login_required
from tcms.rpc.views import rpc_method


@rpc_method(
    name="KiwiTCMS.version",
    auth=django_login_required,
)
def version():
    """
    .. function:: RPC KiwiTCMS.version()

        :return: Current version of Kiwi TCMS installation.
        :rtype: string
    """
    return __version__
