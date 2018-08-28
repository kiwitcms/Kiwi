# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import EnvGroup
from tcms.xmlrpc.utils import parse_bool_value


@rpc_method(name='Env.Group.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Env.Group.filter(query)

        Perform a search and return the resulting list of
        :class:`tcms.management.models.EnvGroup` objects.

        :param query: Field lookups for :class:`tcms.management.models.EnvGroup`
        :type query: dict
        :returns: List of serialized :class:`tcms.management.models.EnvGroup` objects
        :rtype: list(dict)
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return EnvGroup.to_xmlrpc(query)
