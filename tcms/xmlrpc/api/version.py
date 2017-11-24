# -*- coding: utf-8 -*-

from tcms.xmlrpc.decorators import log_call
from tcms.xmlrpc import get_version

__all__ = (
    'get',
)

__xmlrpc_namespace__ = 'Version'


@log_call(namespace=__xmlrpc_namespace__)
def get(request):
    """
    Description: Retrieve XMLRPC's version

    Params:      No parameters.

    Returns:     A list that represents the version.

    Example:
    Version.get()
    """

    return get_version()
