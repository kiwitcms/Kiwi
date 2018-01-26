# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.testcases.models import TestCaseCategory


@rpc_method(name='Category.filter')
def filter(query):
    """
    .. function:: XML-RPC Category.filter(query)

        Search and return TestCaseCategory objects matching query.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCaseCategory`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.TestCaseCategory` objects
        :rtype: list(dict)
    """
    return TestCaseCategory.to_xmlrpc(query)
