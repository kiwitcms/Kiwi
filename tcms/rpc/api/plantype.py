# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.rpc.api.forms.testplan import PlanTypeForm
from tcms.rpc.decorators import permissions_required
from tcms.testplans.models import PlanType

__all__ = (
    "create",
    "filter",
)


@rpc_method(name="PlanType.create")
@permissions_required("testplans.add_plantype")
def create(values):
    """
    .. function:: RPC PlanType.create(values)

        Create a new PlanType object and store it in the database.

        :param values: Field values for :class:`tcms.testplans.models.PlanType`
        :type values: dict
        :return: Serialized :class:`tcms.testplans.models.PlanType` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *testplans.add_plantype* permission
    """
    form = PlanTypeForm(values)
    if form.is_valid():
        plan_type = form.save()
        return model_to_dict(plan_type)

    raise ValueError(form_errors_to_list(form))


@permissions_required("testplans.view_plantype")
@rpc_method(name="PlanType.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC PlanType.filter(query)

        Search and return a list of test plan types.

        :param query: Field lookups for :class:`tcms.testplans.models.PlanType`
        :type query: dict
        :return: Serialized list of :class:`tcms.testplans.models.PlanType` objects
        :rtype: dict
    """
    return list(
        PlanType.objects.filter(**query)
        .values(
            "id",
            "name",
            "description",
        )
        .distinct()
    )
