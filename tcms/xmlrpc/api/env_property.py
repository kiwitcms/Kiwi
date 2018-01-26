# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TCMSEnvProperty
from tcms.xmlrpc.utils import parse_bool_value


@rpc_method(name='Env.Property.filter')
def filter(query):
    """
    .. function:: XML-RPC Env.Property.filter(query)

        Performs a search and returns the resulting list of environment properties.

        :param query: Field lookups for :class:`tcms.management.models.TCMSEnvProperty`
        :type query: dict
        :returns: List of serialized :class:`tcms.management.models.TCMSEnvProperty` objects
        :rtype: list(dict)
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvProperty.to_xmlrpc(query)
