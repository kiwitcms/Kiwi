# -*- coding: utf-8 -*-
from modernrpc.core import rpc_method

from tcms.testcases.models import TestCaseBug


@rpc_method(name='TestCaseBug.filter')
def filter(query):
    """
    .. function:: XML-RPC TestCaseBug.filter(query)

        Get list of bugs that are associated with TestCase or
        a TestCaseRun.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCaseBug`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.TestCaseBug` objects.

        Get all bugs for particular TestCase::

            >>> Bug.filter({'case': 123}) or Bug.filter({'case_id': 123})

        Get all bugs for a particular TestCaseRun::

            >>> Bug.filter({'case_run': 1234}) or Bug.filter({'case_run_id': 1234})
    """
    return TestCaseBug.to_xmlrpc(query)
