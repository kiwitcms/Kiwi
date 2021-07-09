# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.management.forms import VersionForm
from tcms.management.models import Version
from tcms.rpc.decorators import permissions_required

__all__ = (
    "create",
    "filter",
)


@permissions_required("management.view_version")
@rpc_method(name="Version.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Version.filter(query)

        Search and returns the resulting list of versions.

        :param query: Field lookups for :class:`tcms.management.models.Version`
        :type query: dict
        :return: List of serialized :class:`tcms.management.models.Version` objects
        :rtype: list(dict)
    """
    return list(
        Version.objects.filter(**query)
        .values("id", "value", "product", "product__name")
        .order_by("product", "id")
        .distinct()
    )


@permissions_required("management.add_version")
@rpc_method(name="Version.create")
def create(values):
    """
    .. function:: RPC Version.create(values)

        Add new version.

        :param values: Field values for :class:`tcms.management.models.Version`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Version` object
        :rtype: dict
        :raises ValueError: if input data validation fails
        :raises PermissionDenied: if missing *management.add_version* permission

    Example::

        # Add version for specified product:
        >>> Version.create({'value': 'devel', 'product': 272})
        {'id': '1106', 'value': 'devel', 'product': 272}
    """
    form = VersionForm(values)
    if form.is_valid():
        version = form.save()
        return model_to_dict(version)

    raise ValueError(form_errors_to_list(form))
