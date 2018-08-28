# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.testcases.models import Category


@rpc_method(name='Category.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Category.filter(query)

        Search and return Category objects matching query.

        :param query: Field lookups for :class:`tcms.testcases.models.Category`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.Category` objects
        :rtype: list(dict)
    """
    return Category.to_xmlrpc(query)
