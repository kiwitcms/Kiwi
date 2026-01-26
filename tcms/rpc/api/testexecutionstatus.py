# Copyright (c) 2019-2026 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.rpc.api.forms.testrun import TestExecutionStatusForm
from tcms.rpc.decorators import permissions_required
from tcms.testruns.models import TestExecutionStatus


@permissions_required("testruns.view_testexecutionstatus")
@rpc_method(name="TestExecutionStatus.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC TestExecutionStatus.filter(query)

        Search and return the list of test case run statuses.

        :param query: Field lookups for :class:`tcms.testruns.models.TestExecutionStatus`
        :type query: dict
        :return: Serialized list of :class:`tcms.testruns.models.TestExecutionStatus` objects
        :rtype: list(dict)
    """
    return list(
        TestExecutionStatus.objects.filter(**query)
        .values("id", "name", "weight", "icon", "color")
        .order_by("id")
        .distinct()
    )


@permissions_required("testruns.add_testexecutionstatus")
@rpc_method(name="TestExecutionStatus.create")
def create(values):
    """
    .. function:: RPC TestExecutionStatus.create(values)

        Create a new TestExecutionStatus object and store it in the database.

        :param values: Field values for :class:`tcms.testruns.models.TestExecutionStatus`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestExecutionStatus` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *testruns.add_testexecutionstatus* permission

    .. versionadded:: 15.2
    """
    form = TestExecutionStatusForm(values)

    if form.is_valid():
        status = form.save()
        return model_to_dict(status)

    raise ValueError(list(form.errors.items()))
