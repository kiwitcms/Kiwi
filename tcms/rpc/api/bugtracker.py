# Copyright (c) 2025-2026 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.rpc.api.forms.testcase import BugSystemForm
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import BugSystem


@permissions_required("testcases.view_bugsystem")
@rpc_method(name="BugTracker.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC BugTracker.filter(query)

        Perform a search and return the resulting list of bug trackers.

        :param query: Field lookups for :class:`tcms.testcases.models.BugSystem`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.BugSystem` objects
        :rtype: dict
        :raises PermissionDenied: if missing *testcases.view_bugsystem* permission
    """
    return list(
        BugSystem.objects.filter(**query)
        .values(
            "id",
            "name",
            "tracker_type",
            "base_url",
            "api_url",
            "api_username",
            # not exposing this field via RPC b/c it will leak
            # "api_password",
        )
        .order_by("id")
        .distinct()
    )


@permissions_required("testcases.add_bugsystem")
@rpc_method(name="BugTracker.create")
def create(values):
    """
    .. function:: RPC BugTracker.create(values)

        Create a new BugSystem object and store it in the database.

        :param values: Field values for :class:`tcms.testcases.models.BugSystem`
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.BugSystem` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *testcases.add_bugsystem* permission
    """
    form = BugSystemForm(values)

    if form.is_valid():
        bug_system = form.save()
        result = model_to_dict(bug_system)
        # not exposing this field via RPC b/c it will leak
        del result["api_password"]

        return result

    raise ValueError(list(form.errors.items()))
