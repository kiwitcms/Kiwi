# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import Priority


@rpc_method(name='Priority.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Priority.filter(query)

        Perform a search and return the resulting list of priorities.

        :param query: Field lookups for :class:`tcms.management.models.Priority`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Priority` objects
        :rtype: dict
    """
    return Priority.to_xmlrpc(query)
