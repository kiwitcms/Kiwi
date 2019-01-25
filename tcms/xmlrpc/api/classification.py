# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from modernrpc.core import rpc_method

from tcms.management.models import Classification


@rpc_method(name='Classification.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Classification.filter(query)

        Perform a search and return the resulting list of classifications.

        :param query: Field lookups for :class:`tcms.management.models.Classification`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Classification` objects
        :rtype: dict
    """
    return Classification.to_xmlrpc(query)
