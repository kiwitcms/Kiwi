# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.management.forms import ComponentForm
from tcms.management.models import Component
from tcms.rpc.api.forms.management import ComponentUpdateForm
from tcms.rpc.decorators import permissions_required

User = get_user_model()  # pylint: disable=invalid-name


@permissions_required("management.view_component")
@rpc_method(name="Component.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Component.filter(query)

        Search and return the resulting list of components.

        :param query: Field lookups for :class:`tcms.management.models.Component`
        :type query: dict
        :return: List of serialized :class:`tcms.management.models.Component` objects
        :rtype: list(dict)
    """
    return list(
        Component.objects.filter(**query)
        .values(
            "id",
            "name",
            "product",
            "initial_owner",
            "description",
            "cases",
        )
        .order_by("id")
        .distinct()
    )


@permissions_required("management.add_component")
@rpc_method(name="Component.create")
def create(values, **kwargs):
    """
    .. function:: RPC Component.create(values)

        Create new component.

        :param values: Field values for :class:`tcms.management.models.Component`
        :type values: dict
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises ValueError: if data validation fails
        :raises PermissionDenied: if missing *management.add_component* permission

    .. note::

        If ``initial_owner_id`` is not specified this field is set to the
        user issuing the RPC request!
    """
    request = kwargs.get(REQUEST_KEY)
    if "initial_owner" not in values:
        values["initial_owner"] = request.user.pk

    if "description" not in values:
        values["description"] = "Created via API"

    form = ComponentForm(values)

    if form.is_valid():
        component = form.save()
        return model_to_dict(component)

    raise ValueError(list(form.errors.items()))


@permissions_required("management.change_component")
@rpc_method(name="Component.update")
def update(component_id, values):
    """
    .. function:: RPC Component.update

        Update component with new values.

        :param component_id: PK of Component to be updated
        :type component_id: int
        :param values: Fields and values to be updated
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises ValueError: if data validation fails
        :raises PermissionDenied: if missing *management.change_component* permission
    """
    component = Component.objects.get(pk=component_id)
    form = ComponentUpdateForm(values, instance=component)

    if form.is_valid():
        component = form.save()
        return model_to_dict(component)

    raise ValueError(list(form.errors.items()))
