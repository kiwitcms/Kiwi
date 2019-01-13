# -*- coding: utf-8 -*-
from modernrpc.core import rpc_method

from tcms.testcases.models import BugSystem


__all__ = (
    'filter',
)


@rpc_method(name='BugSystem.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC BugSystem.filter(query)

        Get list of bug systems.

        :param query: Field lookups for :class:`tcms.testcases.models.BugSystem`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.BugSystem` objects.
    """
    return BugSystem.to_xmlrpc(query)
