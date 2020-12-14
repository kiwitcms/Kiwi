# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _
from modernrpc.auth.basic import http_basic_auth_login_required
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.rpc.api.utils import tracker_from_url
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import BugSystem
from tcms.testruns.models import TestExecution

__all__ = (
    "details",
    "report",
)


@http_basic_auth_login_required
@rpc_method(name="Bug.details")
def details(url, **kwargs):
    """
    .. function:: RPC Bug.details(url)

        Returns details about bug at the given URL address. This method is
        used when generating additional information which is shown in the UI.

        :param url: URL address
        :type url: str
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Detailed information about this URL. Depends on the underlying
                 issue tracker.
        :rtype: dict
    """
    result = cache.get(url)
    if result:
        return result

    request = kwargs.get(REQUEST_KEY)
    tracker = tracker_from_url(url, request)
    if not tracker:
        return {}

    result = tracker.details(url)
    cache.set(url, result)
    return result


@permissions_required(
    ("testruns.view_testexecution", "linkreference.add_linkreference")
)
@rpc_method(name="Bug.report")
def report(execution_id, tracker_id, **kwargs):
    """
    .. function:: RPC Bug.report(execution_id, tracker_id)

        Returns a URL which will open the bug tracker with predefined fields
        indicating the error was detected by the specified TestExecution.

        :param execution_id: PK for :class:`tcms.testruns.models.TestExecution` object
        :type execution_id: int
        :param tracker_id: PK for :class:`tcms.testcases.models.BugSystem` object
        :type tracker_id: int
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Success response with bug URL or failure message
        :rtype: dict
    """
    request = kwargs.get(REQUEST_KEY)
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
