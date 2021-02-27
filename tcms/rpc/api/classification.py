# Copyright (c) 2019-2021 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from modernrpc.core import rpc_method

from tcms.management.models import Classification
from tcms.rpc.decorators import permissions_required


@permissions_required("management.view_classification")
@rpc_method(name="Classification.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Classification.filter(query)

        Perform a search and return the resulting list of classifications.

        :param query: Field lookups for :class:`tcms.management.models.Classification`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Classification` objects
        :rtype: dict
    """
    return list(Classification.objects.filter(**query).values("id", "name").distinct())
