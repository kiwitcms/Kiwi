# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TestTag


@rpc_method(name='Tag.filter')
def filter(values):
    """
    .. function:: XML-RPC Tag.filter(values)

        Search and return a list of tags

        :param values: Field lookups for :class:`tcms.management.models.TestTag`
        :type values: dict
        :return: Serialized list of :class:`tcms.management.models.TestTag` objects
        :rtype: list(dict)
    """
    return TestTag.to_xmlrpc(values)
