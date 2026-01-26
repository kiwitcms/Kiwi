# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.management.models import Priority
from tcms.rpc.api.forms.management import PriorityForm
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
        Priority.objects.filter(**query)
        .values("id", "value", "is_active")
        .order_by("id")
        .distinct()
    )


@permissions_required("management.add_priority")
@rpc_method(name="Priority.create")
def create(values):
    """
    .. function:: RPC Priority.create(values)

        Create a new Priority object and store it in the database.

        :param values: Field values for :class:`tcms.management.models.Priority`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Priority` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *management.add_priority* permission

    .. versionadded:: 15.2
    """
    form = PriorityForm(values)

    if form.is_valid():
        priority = form.save()
        return model_to_dict(priority)

    raise ValueError(list(form.errors.items()))
