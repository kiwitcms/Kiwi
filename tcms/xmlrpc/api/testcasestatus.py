# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.testcases.models import TestCaseStatus


@rpc_method(name='TestCaseStatus.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC TestCaseStatus.filter(query)

        Search and return the list of test case statuses.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCaseStatus`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.TestCaseStatus` objects
        :rtype: list(dict)
    """
    return TestCaseStatus.to_xmlrpc(query)
