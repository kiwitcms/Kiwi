from django.forms.models import model_to_dict

from tcms.management.forms import ComponentForm
from tcms.management.models import Component
from tcms.rpc.api.forms.management import ComponentUpdateForm
from tcms.rpc.decorators import permissions_required
from tcms.rpc.views import rpc_method


@rpc_method(
    name="Component.filter",
    auth=permissions_required("management.view_component"),
)
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


@rpc_method(
    name="Component.create",
    auth=permissions_required("management.add_component"),
    context_target="rpc_context",
)
def create(values, rpc_context=None):
    """
    .. function:: RPC Component.create(values)

        Create new component.

        :param values: Field values for :class:`tcms.management.models.Component`
        :type values: dict
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises ValueError: if data validation fails
        :raises PermissionDenied: if missing *management.add_component* permission

    .. note::

        If ``initial_owner_id`` is not specified this field is set to the
        user issuing the RPC request!
    """
    request = rpc_context.request
    if "initial_owner" not in values:
        values["initial_owner"] = request.user.pk

    if "description" not in values:
        values["description"] = "Created via API"

    form = ComponentForm(values, request=request)

    if form.is_valid():
        component = form.save()
        return model_to_dict(component)

    raise ValueError(list(form.errors.items()))


@rpc_method(
    name="Component.update",
    auth=permissions_required("management.change_component"),
    context_target="rpc_context",
)
def update(component_id, values, rpc_context=None):
    """
    .. function:: RPC Component.update

        Update component with new values.

        :param component_id: PK of Component to be updated
        :type component_id: int
        :param values: Fields and values to be updated
        :type values: dict
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises ValueError: if data validation fails
        :raises PermissionDenied: if missing *management.change_component* permission
    """
    request = rpc_context.request
    component = Component.objects.get(pk=component_id)
    form = ComponentUpdateForm(values, instance=component, request=request)

    if form.is_valid():
        component = form.save()
        return model_to_dict(component)

    raise ValueError(list(form.errors.items()))
