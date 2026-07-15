from django.core.cache import cache
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from tcms.rpc.api.utils import tracker_from_url
from tcms.rpc.decorators import django_login_required, permissions_required
from tcms.rpc.views import rpc_method
from tcms.testcases.models import BugSystem
from tcms.testruns.models import TestExecution


@rpc_method(
    name="Bug.details",
    auth=django_login_required,
    context_target="rpc_context",
)
def details(url, rpc_context=None):
    """
    .. function:: RPC Bug.details(url)

        Returns details about bug at the given URL address. This method is
        used when generating additional information which is shown in the UI.

        :param url: URL address
        :type url: str
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Detailed information about this URL. Depends on the underlying
                 issue tracker.
        :rtype: dict
    """
    result = cache.get(url)
    if result:
        return result

    request = rpc_context.request
    tracker = tracker_from_url(url, request)
    if not tracker:
        return {}

    result = dict(tracker.details(url))
    cache.set(url, result)
    return result


@rpc_method(
    name="Bug.report",
    auth=permissions_required(
        "testruns.view_testexecution", "linkreference.add_linkreference"
    ),
    context_target="rpc_context",
)
def report(execution_id, tracker_id, rpc_context=None):
    """
    .. function:: RPC Bug.report(execution_id, tracker_id)

        Returns a URL which will open the bug tracker with predefined fields
        indicating the error was detected by the specified TestExecution.

        :param execution_id: PK for :class:`tcms.testruns.models.TestExecution` object
        :type execution_id: int
        :param tracker_id: PK for :class:`tcms.testcases.models.BugSystem` object
        :type tracker_id: int
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Success response with bug URL or failure message
        :rtype: dict
    """
    request = rpc_context.request
    response = {
        "rc": 1,
        "response": _(
            "Enable reporting to this Issue Tracker by configuring its base_url!"
        ),
    }

    execution = TestExecution.objects.get(pk=execution_id)
    bug_system = BugSystem.objects.get(pk=tracker_id)
    tracker = import_string(bug_system.tracker_type)(bug_system, request)
    if not tracker.is_adding_testcase_to_issue_disabled():
        url = tracker.report_issue_from_testexecution(execution, request.user)
        response = {"rc": 0, "response": url}

    return response
