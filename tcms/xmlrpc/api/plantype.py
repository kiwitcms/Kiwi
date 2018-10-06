# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.testplans.models import PlanType


@rpc_method(name='PlanType.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC PlanType.filter(query)

        Search and return a list of test plan types.

        :param query: Field lookups for :class:`tcms.testplans.models.PlanType`
        :type query: dict
        :return: Serialized list of :class:`tcms.testplans.models.PlanType` objects
        :rtype: dict
    """
    return PlanType.to_xmlrpc(query)
