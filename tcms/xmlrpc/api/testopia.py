# -*- coding: utf-8 -*-

from tcms.xmlrpc.decorators import log_call

__xmlrpc_namespace__ = 'Testopia'


@log_call(namespace=__xmlrpc_namespace__)
def api_version(request):
    """
    Description: Return the API version of Nitrate.
    """
    from tcms import XMLRPC_VERSION

    return XMLRPC_VERSION


@log_call(namespace=__xmlrpc_namespace__)
def testopia_version(request):
    """
    Description: Returns the version of Nitrate on this server.
    """
    from tcms import VERSION

    return VERSION


@log_call(namespace=__xmlrpc_namespace__)
def nitrate_version(request):
    """
    Description: Returns the version of Nitrate on this server.
    """
    from tcms import VERSION

    return VERSION


@log_call(namespace=__xmlrpc_namespace__)
def tcms_version(request):
    """
    Description: Returns the version of Nitrate on this server.
    """
    from tcms import VERSION

    return VERSION
