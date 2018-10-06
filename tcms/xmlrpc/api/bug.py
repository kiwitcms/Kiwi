# -*- coding: utf-8 -*-
from modernrpc.core import rpc_method

from tcms.testcases.models import Bug
from tcms.xmlrpc.decorators import permissions_required


__all__ = (
    'create',
    'remove',
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
def create(values):
    """
    .. function:: XML-RPC Bug.create(values)

        Attach a bug to pre-existing TestCase or TestCaseRun object.

        :param values: Field values for :class:`tcms.testcases.models.Bug`
        :type values: dict
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
    return bug.serialize()


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
