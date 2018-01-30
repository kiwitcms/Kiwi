# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.testplans.models import TestPlanType


@rpc_method(name='PlanType.filter')
def filter(query):
    """
    .. function:: PlanType.filter(query)

        Search and return a list of test plan types.

        :param query: Field lookups for :class:`tcms.testplans.models.TestPlanType`
        :type query: dict
        :return: Serialized list of :class:`tcms.testplans.models.TestPlanType` objects
        :rtype: dict
    """
    return TestPlanType.to_xmlrpc(query)
