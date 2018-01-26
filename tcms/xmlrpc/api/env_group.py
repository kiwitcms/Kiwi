# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TCMSEnvGroup
from tcms.xmlrpc.utils import parse_bool_value


@rpc_method(name='Env.Group.filter')
def filter(query):
    """
    .. function:: XML-RPC Env.Group.filter(query)

        Perform a search and return the resulting list of
        :class:`tcms.management.models.TCMSEnvGroup` objects.

        :param query: Field lookups for :class:`tcms.management.models.TCMSEnvGroup`
        :type query: dict
        :returns: List of serialized :class:`tcms.management.models.TCMSEnvGroup` objects
        :rtype: list(dict)
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvGroup.to_xmlrpc(query)
