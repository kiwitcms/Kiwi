# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import Product
from tcms.xmlrpc.decorators import permissions_required


__all__ = (
    'create',
    'filter',
)


@rpc_method(name='Product.create')
@permissions_required('management.add_product')
def create(values):
    """
    .. function:: XML-RPC Product.create(values)

        Create a new Product object and store it in the database.

        :param values: Field values for :class:`tcms.management.models.Product`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Product` object
        :rtype: dict
        :raises: PermissionDenied if missing *management.add_product* permission
    """
    return Product.objects.create(**values).serialize()


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
