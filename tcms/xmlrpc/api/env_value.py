# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TCMSEnvValue
from tcms.xmlrpc.utils import parse_bool_value


@rpc_method(name='Env.Value.filter')
def filter(query):
    """
    .. function:: XML-RPC Env.Value.filter(query)

        Performs a search and returns the resulting list of environment values.

        :param query: Field lookups for :class:`tcms.management.models.TCMSEnvValue`
        :type query: dict
        :returns: List of serialized :class:`tcms.management.models.TCMSEnvValue` objects
        :rtype: list(dict)
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvValue.to_xmlrpc(query)
