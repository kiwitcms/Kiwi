# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import EnvValue
from tcms.xmlrpc.utils import parse_bool_value


@rpc_method(name='Env.Value.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Env.Value.filter(query)

        Performs a search and returns the resulting list of environment values.

        :param query: Field lookups for :class:`tcms.management.models.EnvValue`
        :type query: dict
        :returns: List of serialized :class:`tcms.management.models.EnvValue` objects
        :rtype: list(dict)
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return EnvValue.to_xmlrpc(query)
