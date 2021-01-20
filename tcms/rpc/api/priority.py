# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import Priority
from tcms.rpc.decorators import permissions_required


@permissions_required("management.view_priority")
@rpc_method(name="Priority.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Priority.filter(query)

        Perform a search and return the resulting list of priorities.

        :param query: Field lookups for :class:`tcms.management.models.Priority`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Priority` objects
        :rtype: dict
    """
    return list(
        Priority.objects.filter(**query).values("id", "value", "is_active").distinct()
    )
