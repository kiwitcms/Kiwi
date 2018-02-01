# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TestTag


@rpc_method(name='Tag.filter')
def filter(query):
    """
    .. function:: XML-RPC Tag.filter(query)

        Search and return a list of tags

        :param query: Field lookups for :class:`tcms.management.models.TestTag`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.TestTag` objects
        :rtype: list(dict)
    """
    return TestTag.to_xmlrpc(query)
