# -*- coding: utf-8 -*-
from modernrpc.core import rpc_method

from django.utils.translation import ugettext_lazy as _

from tcms.testcases.models import Bug
from tcms.testcases.models import BugSystem
from tcms.testruns.models import TestExecution
from tcms.issuetracker.types import IssueTrackerType
from tcms.xmlrpc.decorators import permissions_required


__all__ = (
    'create',
    'remove',
    'report',
    'filter',
)


@rpc_method(name='Bug.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Bug.filter(query)

        Get list of bugs that are associated with TestCase or
        a TestCaseRun.

        :param query: Field lookups for :class:`tcms.testcases.models.Bug`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.Bug` objects.

        Get all bugs for particular TestCase::

            >>> Bug.filter({'case': 123}) or Bug.filter({'case_id': 123})

        Get all bugs for a particular TestCaseRun::

            >>> Bug.filter({'case_run': 1234}) or Bug.filter({'case_run_id': 1234})
    """
    return Bug.to_xmlrpc(query)


@permissions_required('testcases.add_bug')
@rpc_method(name='Bug.create')
def create(values, auto_report=False):
    """
    .. function:: XML-RPC Bug.create(values, auto_report=False)

        Attach a bug to pre-existing TestCase or TestCaseRun object.

        :param values: Field values for :class:`tcms.testcases.models.Bug`
        :type values: dict
        :param auto_report: Automatically report to Issue Tracker
        :type auto_report: bool, default=False
        :return: Serialized :class:`tcms.testcases.models.Bug` object
        :raises: PermissionDenied if missing the *testcases.add_bug* permission

        .. note::

            `case_run_id` can be None. In this case the bug will be attached only
            to the TestCase with specified `case_id`.

        Example (doesn't specify case_run_id)::

            >>> Bug.create({
                'case_id': 12345,
                'bug_id': 67890,
                'bug_system_id': 1,
                'summary': 'Testing TCMS',
                'description': 'Just foo and bar',
            })
    """
    bug, _ = Bug.objects.get_or_create(**values)
    response = bug.serialize()
    response['rc'] = 0

    if auto_report:
        tracker = IssueTrackerType.from_name(bug.bug_system.tracker_type)(bug.bug_system)

        if not tracker.is_adding_testcase_to_issue_disabled():
            tracker.add_testcase_to_issue([bug.case], bug)
        else:
            response['rc'] = 1
            response['response'] = _('Enable linking test cases by configuring '
                                     'API parameters for this Issue Tracker!')
    return response


@permissions_required('testcases.delete_bug')
@rpc_method(name='Bug.remove')
def remove(query):
    """
    .. function:: XML-RPC Bug.remove(query)

        Remove bugs from pre-existing TestCase or TestCaseRun object(s).

        :param query: Field lookups for :class:`tcms.testcases.models.Bug`
        :type query: dict
        :return: None
        :raises: PermissionDenied if missing the *testcases.delete_bug* permission

        Example - removing bug from TestCase::

            >>> Bug.remove({
                'case_id': 12345,
                'bug_id': 67890,
                'case_run__isnull': True
            })

        Example - removing bug from TestCaseRun (specify case_run_id)::

            >>> Bug.remove({
                'bug_id': 67890,
                'case_run_id': 99999,
            })
    """
    return Bug.objects.filter(**query).delete()


@rpc_method(name='Bug.report')
def report(test_case_run_id, tracker_id):
    """
    .. function:: XML-RPC Bug.report(test_case_run_id, tracker_id)

        Returns a URL which will open the bug tracker with predefined fields
        indicating the error was detected by the specified TestCaseRun.

        :param test_case_run_id: PK for :class:`tcms.testruns.models.TestCaseRun` object
        :type test_case_run_id: int
        :param tracker_id: PK for :class:`tcms.testcases.models.BugSystem` object
        :type tracker_id: int
        :return: Success response with bug URL or failure message
        :rtype: dict
    """
    response = {
        'rc': 1,
        'response': _('Enable reporting to this Issue Tracker by configuring its base_url!'),
    }

    test_case_run = TestExecution.objects.get(pk=test_case_run_id)
    bug_system = BugSystem.objects.get(pk=tracker_id)
    if bug_system.base_url:
        tracker = IssueTrackerType.from_name(bug_system.tracker_type)(bug_system)
        url = tracker.report_issue_from_testcase(test_case_run)
        response = {'rc': 0, 'response': url}

    return response
