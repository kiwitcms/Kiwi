# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import Product


@rpc_method(name='Product.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Product.filter(query)

        Perform a search and return the resulting list of products.

        :param query: Field lookups for :class:`tcms.management.models.Product`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Product` objects
        :rtype: dict

    Example::

        # Get all of products named 'Red Hat Enterprise Linux 5'
        >>> Product.filter({'name': 'Red Hat Enterprise Linux 5'})
    """
    return Product.to_xmlrpc(query)
