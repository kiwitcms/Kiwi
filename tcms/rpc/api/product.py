# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.management.models import Product
from tcms.rpc.api.forms.management import ProductForm
from tcms.rpc.decorators import permissions_required

__all__ = (
    "create",
    "filter",
)


@rpc_method(name="Product.create")
@permissions_required("management.add_product")
def create(values):
    """
    .. function:: RPC Product.create(values)

        Create a new Product object and store it in the database.

        :param values: Field values for :class:`tcms.management.models.Product`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Product` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *management.add_product* permission
    """
    form = ProductForm(values)

    if form.is_valid():
        product = form.save()
        return model_to_dict(product)

    raise ValueError(form_errors_to_list(form))


@permissions_required("management.view_product")
@rpc_method(name="Product.filter")
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Product.filter(query)

        Perform a search and return the resulting list of products.

        :param query: Field lookups for :class:`tcms.management.models.Product`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Product` objects
        :rtype: dict

    Example::

        # Get all of products named 'Red Hat Enterprise Linux 5'
        >>> Product.filter({'name': 'Red Hat Enterprise Linux 5'})
    """
    if query is None:
        query = {}

    return list(
        Product.objects.filter(**query)
        .values(
            "id",
            "name",
            "description",
            "classification",
        )
        .distinct()
        .order_by("pk")
    )
