# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import TestCaseStatus


@permissions_required("testcases.view_testcasestatus")
@rpc_method(name="TestCaseStatus.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC TestCaseStatus.filter(query)

        Search and return the list of test case statuses.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCaseStatus`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.TestCaseStatus` objects
        :rtype: list(dict)
    """
    return TestCaseStatus.to_xmlrpc(query)
