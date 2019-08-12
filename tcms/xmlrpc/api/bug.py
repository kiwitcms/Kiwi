# -*- coding: utf-8 -*-
from modernrpc.core import rpc_method

from django.utils.translation import ugettext_lazy as _

from tcms.testcases.models import BugSystem
from tcms.testruns.models import TestExecution
from tcms.issuetracker.types import IssueTrackerType


__all__ = (
    'report',
)


@rpc_method(name='Bug.report')
def report(execution_id, tracker_id):
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
    response = {
        'rc': 1,
        'response': _('Enable reporting to this Issue Tracker by configuring its base_url!'),
    }

    execution = TestExecution.objects.get(pk=execution_id)
    bug_system = BugSystem.objects.get(pk=tracker_id)
    if bug_system.base_url:
        tracker = IssueTrackerType.from_name(bug_system.tracker_type)(bug_system)
        url = tracker.report_issue_from_testcase(execution)
        response = {'rc': 0, 'response': url}

    return response
