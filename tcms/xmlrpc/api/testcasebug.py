# -*- coding: utf-8 -*-
from modernrpc.core import rpc_method

from tcms.testcases.models import TestCaseBug
from tcms.xmlrpc.decorators import permissions_required


__all__ = (
    'create',
    'remove',
    'filter',
)


@rpc_method(name='TestCaseBug.filter')
def filter(query):
    """
    .. function:: XML-RPC TestCaseBug.filter(query)

        Get list of bugs that are associated with TestCase or
        a TestCaseRun.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCaseBug`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.TestCaseBug` objects.

        Get all bugs for particular TestCase::

            >>> Bug.filter({'case': 123}) or Bug.filter({'case_id': 123})

        Get all bugs for a particular TestCaseRun::

            >>> Bug.filter({'case_run': 1234}) or Bug.filter({'case_run_id': 1234})
    """
    return TestCaseBug.to_xmlrpc(query)


@permissions_required('testcases.add_testcasebug')
@rpc_method(name='TestCaseBug.create')
def create(values):
    """
    .. function:: XML-RPC TestCaseBug.create(values)

        Attach a bug to pre-existing TestCase or TestCaseRun object.

        :param values: Field values for :class:`tcms.testcases.models.TestCaseBug`
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.TestCaseBug` object
        :raises: PermissionDenied if missing the *testcases.add_testcasebug* permission

        .. note::

            `case_run_id` can be None. In this case the bug will be attached only
            to the TestCase with specified `case_id`.

        Example (doesn't specify case_run_id)::

            >>> TestCaseBug.create({
                'case_id': 12345,
                'bug_id': 67890,
                'bug_system_id': 1,
                'summary': 'Testing TCMS',
                'description': 'Just foo and bar',
            })
    """
    bug, _ = TestCaseBug.objects.get_or_create(**values)
    return bug.serialize()


@permissions_required('testcases.delete_testcasebug')
@rpc_method(name='TestCaseBug.remove')
def remove(query):
    """
    .. function:: XML-RPC TestCaseBug.remove(query)

        Remove bugs from pre-existing TestCase or TestCaseRun object(s).

        :param query: Field lookups for :class:`tcms.testcases.models.TestCaseBug`
        :type query: dict
        :return: None
        :raises: PermissionDenied if missing the *testcases.delete_testcasebug* permission

        Example - removing bug from TestCase::

            >>> TestCaseBug.remove({
                'case_id': 12345,
                'bug_id': 67890,
                'case_run__isnull': True
            })

        Example - removing bug from TestCaseRun (specify case_run_id)::

            >>> TestCaseBug.remove({
                'bug_id': 67890,
                'case_run_id': 99999,
            })
    """
    return TestCaseBug.objects.filter(**query).delete()
