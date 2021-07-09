# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.management.models import Build
from tcms.rpc.api.forms.management import BuildForm, BuildUpdateForm
from tcms.rpc.decorators import permissions_required

__all__ = (
    "create",
    "update",
    "filter",
)


@permissions_required("management.view_build")
@rpc_method(name="Build.filter")
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Build.filter(query)

        Search and return builds matching query.

        :param query: Field lookups for :class:`tcms.management.models.Build`
        :type query: dict
        :return: List of serialized :class:`tcms.management.models.Build` objects
        :rtype: list(dict)
    """

    if query is None:
        query = {}
    return list(
        Build.objects.filter(**query)
        .values(
            "id",
            "name",
            "version",
            "version__value",
            "is_active",
        )
        .order_by("version", "id")
        .distinct()
    )


@rpc_method(name="Build.create")
@permissions_required("management.add_build")
def create(values):
    """
    .. function:: RPC Build.create(values)

        Create a new build object and store it in the database.

        :param values: Field values for :class:`tcms.management.models.Build`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Build` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *management.add_build* permission
    """
    if "is_active" not in values:
        values["is_active"] = True

    form = BuildForm(values)
    if form.is_valid():
        build = form.save()
        return model_to_dict(build)

    raise ValueError(form_errors_to_list(form))


@permissions_required("management.change_build")
@rpc_method(name="Build.update")
def update(build_id, values):
    """
    .. function:: RPC Build.update(build_id, values)

        Updates the fields of the selected build.

        :param build_id: PK of Build to modify
        :type build_id: int
        :param values: Field values for :class:`tcms.management.models.Build`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Build` object
        :rtype: dict
        :raises Build.DoesNotExist: if build not found
        :raises PermissionDenied: if missing *management.change_build* permission
        :raises ValueError: if input values don't validate
    """
    build = Build.objects.get(pk=build_id)
    form = BuildUpdateForm(values, instance=build)

    if form.is_valid():
        build = form.save()
        return model_to_dict(build)

    raise ValueError(form_errors_to_list(form))
