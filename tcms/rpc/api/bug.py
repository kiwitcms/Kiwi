# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.issuetracker.types import from_name
from tcms.rpc.api.utils import tracker_from_url
from tcms.testcases.models import BugSystem
from tcms.testruns.models import TestExecution

__all__ = (
    'details',
    'report',
)


@rpc_method(name='Bug.details')
def details(url):
    """
    .. function:: XML-RPC Bug.details(url)

        Returns details about bug at the given URL address. This method is
        used when generating additional information which is shown in the UI.

        :param url: URL address
        :type url: str
        :return: Detailed information about this URL. Depends on the underlying
                 issue tracker.
        :rtype: dict
    """
    result = cache.get(url)
    if not result:
        tracker = tracker_from_url(url)
        result = tracker.details(url)
        cache.set(url, result)

    return result


@rpc_method(name='Bug.report')
def report(execution_id, tracker_id, **kwargs):
    """
    .. function:: XML-RPC Bug.report(execution_id, tracker_id)

        Returns a URL which will open the bug tracker with predefined fields
        indicating the error was detected by the specified TestExecution.

        :param execution_id: PK for :class:`tcms.testruns.models.TestExecution` object
        :type execution_id: int
        :param tracker_id: PK for :class:`tcms.testcases.models.BugSystem` object
        :type tracker_id: int
        :return: Success response with bug URL or failure message
        :rtype: dict
    """
    request = kwargs.get(REQUEST_KEY)
    response = {
        'rc': 1,
        'response': _('Enable reporting to this Issue Tracker by configuring its base_url!'),
    }

    execution = TestExecution.objects.get(pk=execution_id)
    bug_system = BugSystem.objects.get(pk=tracker_id)
    tracker = from_name(bug_system.tracker_type)(bug_system)
    if not tracker.is_adding_testcase_to_issue_disabled():
        url = tracker.report_issue_from_testexecution(execution, request.user)
        response = {'rc': 0, 'response': url}

    return response
