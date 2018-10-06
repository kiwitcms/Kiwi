# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import Tag


@rpc_method(name='Tag.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Tag.filter(query)

        Search and return a list of tags

        :param query: Field lookups for :class:`tcms.management.models.Tag`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Tag` objects
        :rtype: list(dict)
    """
    return Tag.to_xmlrpc(query)
