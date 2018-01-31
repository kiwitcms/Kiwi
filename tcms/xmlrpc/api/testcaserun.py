# -*- coding: utf-8 -*-
from django.db.models import ObjectDoesNotExist
from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.core.utils import form_errors_to_list
from tcms.core.contrib.linkreference.views import create_link
from tcms.core.contrib.linkreference.models import LinkReference
from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.testcases.models import TestCaseBug
from tcms.testruns.models import TestCaseRun
from tcms.xmlrpc.utils import pre_process_ids
from tcms.xmlrpc.utils import Comment
from tcms.xmlrpc.decorators import permissions_required

__all__ = (
    'add_log',
    'remove_log',
    'get_logs',

    'create',
    'filter',
    'update',

    'add_comment',
    'attach_bug',
    'detach_bug',
    'get_bugs',
)


@rpc_method(name='TestCaseRun.add_comment')
def add_comment(case_run_id, comment, **kwargs):
    """
    .. function:: XML-RPC TestCaseRun.add_comment(case_run_id, comment)

        Add comment to selected test case run.

        :param case_run_id: PK of a TestCaseRun object
        :param case_run_id: int
        :param comment: The text to add as a comment
        :param comment: str
        :return: None
    """
    Comment(
        request=kwargs.get(REQUEST_KEY),
        content_type='testruns.testcaserun',
        object_pks=[case_run_id],
        comment=comment
    ).add()


@permissions_required('testcases.add_testcasebug')
@rpc_method(name='TestCaseRun.attach_bug')
def attach_bug(values):
    """
    Description: Add one or more bugs to the selected test cases.

    Params:     $values - Array/Hash: A reference to a hash or array of hashes with keys and values
                                      matching the fields of the test case bug to be created.

      +-------------------+----------------+-----------+------------------------+
      | Field             | Type           | Null      | Description            |
      +-------------------+----------------+-----------+------------------------+
      | case_run_id       | Integer        | Required  | ID of Case             |
      | bug_id            | Integer        | Required  | ID of Bug              |
      | bug_system_id     | Integer        | Required  | 1: BZ(Default), 2: JIRA|
      | summary           | String         | Optional  | Bug summary            |
      | description       | String         | Optional  | Bug description        |
      +-------------------+----------------+-----------+------------------------+

    Returns:     Array: empty on success or an array of hashes with failure
                 codes if a failure occured.

    Example:
    >>> TestCaseRun.attach_bug({
        'case_run_id': 12345,
        'bug_id': 67890,
        'bug_system_id': 1,
        'summary': 'Testing TCMS',
        'description': 'Just foo and bar',
    })
    """
    from tcms.testcases.models import TestCaseBugSystem
    from tcms.xmlrpc.forms import AttachCaseRunBugForm

    if isinstance(values, dict):
        values = [values, ]

    for value in values:

        form = AttachCaseRunBugForm(value)
        if form.is_valid():
            bug_system = TestCaseBugSystem.objects.get(
                id=form.cleaned_data['bug_system_id'])
            tcr = TestCaseRun.objects.only('pk', 'case').get(
                case_run_id=form.cleaned_data['case_run_id'])
            tcr.add_bug(
                bug_id=form.cleaned_data['bug_id'],
                bug_system_id=bug_system.pk,
                summary=form.cleaned_data['summary'],
                description=form.cleaned_data['description']
            )
        else:
            raise ValueError(form_errors_to_list(form))
    return


@permissions_required('testruns.add_testcaserun')
@rpc_method(name='TestCaseRun.create')
def create(values):
    """
    .. function:: XML-RPC TestCaseRun.create(values)

        Create new TestCaseRun object and store it in the database.

        :param values: Field values for :class:`tcms.testruns.models.TestCaseRun`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestCaseRun` object
        :raises: PermissionDenied if missing *testruns.add_testcaserun* permission

        Minimal parameters::

            >>> values = {
                'run': 1990,
                'case': 12345,
                'build': 123,
            }
            >>> TestCaseRun.create(values)
    """
    from tcms.testruns.forms import XMLRPCNewCaseRunForm

    form = XMLRPCNewCaseRunForm(values)

    if not isinstance(values, dict):
        raise TypeError('Argument values must be in dict type.')
    if not values:
        raise ValueError('Argument values is empty.')

    if form.is_valid():
        tr = form.cleaned_data['run']

        tcr = tr.add_case_run(
            case=form.cleaned_data['case'],
            build=form.cleaned_data['build'],
            assignee=form.cleaned_data['assignee'],
            case_run_status=form.cleaned_data['case_run_status'],
            case_text_version=form.cleaned_data['case_text_version'],
            notes=form.cleaned_data['notes'],
            sortkey=form.cleaned_data['sortkey']
        )
    else:
        raise ValueError(form_errors_to_list(form))

    return tcr.serialize()


@permissions_required('testcases.delete_testcasebug')
@rpc_method(name='TestCaseRun.detach_bug')
def detach_bug(case_run_ids, bug_ids):
    """
    Description: Remove one or more bugs to the selected test case-runs.

    Params:      $case_run_ids - Integer/Array/String: An integer or alias representing the ID
                                                       in the database, an array of case_run_ids,
                                                       or a string of comma separated case_run_ids.

                 $bug_ids - Integer/Array/String: An integer representing the ID in the database,
                        an array of bug_ids, or a string of comma separated primary key of bug_ids.

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occured.

    Example:
    # Remove bug id 54321 from case 1234
    >>> TestCaseRun.detach_bug(1234, 54321)
    # Remove bug ids list [1234, 5678] from cases list [56789, 12345]
    >>> TestCaseRun.detach_bug([56789, 12345], [1234, 5678])
    # Remove bug ids list '1234, 5678' from cases list '56789, 12345' with String
    >>> TestCaseRun.detach_bug('56789, 12345', '1234, 5678')
    """
    tcrs = TestCaseRun.objects.filter(
        case_run_id__in=pre_process_ids(case_run_ids)
    )
    bug_ids = pre_process_ids(bug_ids)

    for tcr in tcrs.iterator():
        case_run_id = tcr.case_run_id
        for opk in bug_ids:
            try:
                tcr.remove_bug(bug_id=opk, run_id=case_run_id)
            except ObjectDoesNotExist:
                pass

    return


@rpc_method(name='TestCaseRun.filter')
def filter(values):
    """
    .. function:: XML-RPC TestCaseRun.filter(values)

        Perform a search and return the resulting list of test case executions.

        :param values: Field lookups for :class:`tcms.testruns.models.TestCaseRun`
        :type values: dict
        :return: List of serialized :class:`tcms.testruns.models.TestCaseRun` objects
        :rtype: list(dict)
    """
    return TestCaseRun.to_xmlrpc(values)


@rpc_method(name='TestCaseRun.get_bugs')
def get_bugs(query):
    """
TODO: duplicate with TestCase.get_bugs

    Description: Get the list of bugs that are associated with this test case.

    Params:      $query - dict

    Returns:     Array: An array of bug object hashes.

    Example:
    >>> TestCase.get_bugs(12345)
    """
    return TestCaseBug.to_xmlrpc(query)


@permissions_required('testruns.change_testcaserun')
@rpc_method(name='TestCaseRun.update')
def update(case_run_id, values, **kwargs):
    """
    .. function:: XML-RPC TestCaseRun.update(case_run_id, values)

        Update the selected TestCaseRun

        :param case_run_id: PK of TestCaseRun to modify
        :type case_run_id: int
        :param values: Field values for :class:`tcms.testruns.models.TestCaseRun`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestCaseRun` object
        :raises: PermissionDenied if missing *testruns.change_testcaserun* permission
    """
    from tcms.testruns.forms import XMLRPCUpdateCaseRunForm

    tcr = TestCaseRun.objects.get(pk=case_run_id)
    form = XMLRPCUpdateCaseRunForm(values)

    if form.is_valid():
        if form.cleaned_data['build']:
            tcr.build = form.cleaned_data['build']

        if form.cleaned_data['assignee']:
            tcr.assignee = form.cleaned_data['assignee']

        if form.cleaned_data['case_run_status']:
            tcr.case_run_status = form.cleaned_data['case_run_status']
            request = kwargs.get(REQUEST_KEY)
            tcr.tested_by = request.user

        if 'notes' in values:
            if values['notes'] in (None, ''):
                tcr.notes = values['notes']
            if form.cleaned_data['notes']:
                tcr.notes = form.cleaned_data['notes']

        if form.cleaned_data['sortkey'] is not None:
            tcr.sortkey = form.cleaned_data['sortkey']

        tcr.save()

    else:
        raise ValueError(form_errors_to_list(form))

    return tcr.serialize()


@rpc_method(name='TestCaseRun.add_log')
def add_log(case_run_id, name, url):
    """
    .. function:: XML-RPC TestCaseRun.add_log(case_run_id, name, url)

        Add new log link to a TestCaseRun

        :param case_run_id: PK of a TestCaseRun object
        :type case_run_id: int
        :param name: Name/description of the log
        :type name: str
        :param url: URL of the log
        :type url: str
        :return: ID of created log link
        :rtype: int
        :raises: RuntimeError if operation not successfull
    """
    result = create_link({
        'name': name,
        'url': url,
        'target': 'TestCaseRun',
        'target_id': case_run_id
    })
    if result['rc'] != 0:
        raise RuntimeError(result['response'])
    return result['data']['pk']


@rpc_method(name='TestCaseRun.remove_log')
def remove_log(case_run_id, link_id):
    """
    .. function:: XML-RPC TestCaseRun.remove_log(case_run_id, link_id)

        Remove log link from TestCaseRun

        :param case_run_id: PK of TestCaseRun to modify
        :type case_run_id: int
        :param link_id: PK of link to remove
        :type link_id: int
        :return: None
    """
    LinkReference.objects.filter(pk=link_id, test_case_run=case_run_id).delete()


@rpc_method(name='TestCaseRun.get_logs')
def get_logs(case_run_id):
    """
    .. function:: XML-RPC TestCaseRun.get_logs(case_run_id)

        Get log links for the specified TestCaseRun

        :param case_run_id: PK of TestCaseRun object
        :type case_run_id: int
        :return: Serialized list of :class:`tcms.core.contrib.linkreference.models.LinkReference`
                 objects
    """
    links = LinkReference.objects.filter(test_case_run=case_run_id)
    s = XMLRPCSerializer(links)
    return s.serialize_queryset()
