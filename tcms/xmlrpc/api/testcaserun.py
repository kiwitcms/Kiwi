# -*- coding: utf-8 -*-

from django.db.models import ObjectDoesNotExist
from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.core.contrib.linkreference.models import create_link, LinkReference
from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.testcases.models import TestCaseBug
from tcms.testruns.models import TestCaseRun, TestCaseRunStatus
from tcms.xmlrpc.utils import pre_process_ids
from tcms.xmlrpc.decorators import permissions_required

__all__ = (
    'add_comment',
    'attach_bug',
    'attach_log',
    'get_case_run_status_by_name',
    'create',
    'detach_bug',
    'detach_log',
    'filter',
    'get',
    'get_bugs',
    'get_logs',
    'update',
)


@rpc_method(name='TestCaseRun.add_comment')
def add_comment(case_run_ids, comment, **kwargs):
    """
    Description: Adds comments to selected test case runs.

    Params:      $case_run_ids - Integer/Array/String: An integer representing the ID
                             in the database, an array of case_run_ids, or a string of
                             comma separated case_run_ids.

                 $comment - String - The comment

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occured.

    Example:
    # Add comment 'foobar' to case run 1234
    >>> TestCaseRun.add_comment(1234, 'foobar')
    # Add 'foobar' to case runs list [56789, 12345]
    >>> TestCaseRun.add_comment([56789, 12345], 'foobar')
    # Add 'foobar' to case runs list '56789, 12345' with String
    >>> TestCaseRun.add_comment('56789, 12345', 'foobar')
    """
    from tcms.xmlrpc.utils import Comment

    # FIXME: empty object_pks should be an ValueError
    object_pks = pre_process_ids(value=case_run_ids)
    request = kwargs.get(REQUEST_KEY)
    c = Comment(
        request=request,
        content_type='testruns.testcaserun',
        object_pks=object_pks,
        comment=comment
    )

    return c.add()


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
    from tcms.core import forms
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
            raise ValueError(forms.errors_to_list(form))
    return


@rpc_method(name='TestCaseRun.get_case_run_status_by_name')
def get_case_run_status_by_name(name):
    """
    Params:      $name - String: the status name.

    Returns:     Hash: Matching case run status object hash or error if not found.

    Example:
    >>> TestCaseRun.check_case_run_status('idle')
    """
    return TestCaseRunStatus.objects.get(name=name).serialize()


@permissions_required('testruns.add_testcaserun')
@rpc_method(name='TestCaseRun.create')
def create(values):
    """
    *** It always report - ValueError: invalid literal for int() with base 10: '' ***

    Description: Creates a new Test Case Run object and stores it in the database.

    Params:      $values - Hash: A reference to a hash with keys and values
                           matching the fields of the test case to be created.
  +--------------------+----------------+-----------+---------------------------------------+
  | Field              | Type           | Null      | Description                           |
  +--------------------+----------------+-----------+---------------------------------------+
  | run                | Integer        | Required  | ID of Test Run                        |
  | case               | Integer        | Required  | ID of test case                       |
  | build              | Integer        | Required  | ID of a Build in plan's product       |
  | assignee           | Integer        | Optional  | ID of assignee                        |
  | case_run_status    | Integer        | Optional  | Defaults to "IDLE"                    |
  | case_text_version  | Integer        | Optional  | Default to latest case text version   |
  | notes              | String         | Optional  |                                       |
  | sortkey            | Integer        | Optional  | a.k.a. Index, Default to 0            |
  +--------------------+----------------+-----------+---------------------------------------+

    Returns:     The newly created object hash.

    Example:
    # Minimal test case parameters
    >>> values = {
        'run': 1990,
        'case': 12345,
        'build': 123,
    }
    >>> TestCaseRun.create(values)
    """
    from tcms.core import forms
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
        raise ValueError(forms.errors_to_list(form))

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
def filter(values={}):
    """
    Description: Performs a search and returns the resulting list of test cases.

    Params:      $values - Hash: keys must match valid search fields.

        +----------------------------------------------------------------+
        |               Case-Run Search Parameters                       |
        +----------------------------------------------------------------+
        |        Key          |          Valid Values                    |
        | case_run_id         | Integer                                  |
        | assignee            | ForeignKey: Auth.User                    |
        | build               | ForeignKey: Build                        |
        | case                | ForeignKey: Test Case                    |
        | case_run_status     | ForeignKey: Case Run Status              |
        | notes               | String                                   |
        | run                 | ForeignKey: Test Run                     |
        | tested_by           | ForeignKey: Auth.User                    |
        | running_date        | Datetime                                 |
        | close_date          | Datetime                                 |
        +----------------------------------------------------------------+

    Returns:     Object: Matching test cases are retuned in a list of hashes.

    Example:
    # Get all case runs contain 'TCMS' in case summary
    >>> TestCaseRun.filter({'case__summary__icontain': 'TCMS'})
    """
    return TestCaseRun.to_xmlrpc(values)


@rpc_method(name='TestCaseRun.get')
def get(query):
    """
    Description: Used to load an existing test case-run from the database.

    Params:      query - dict

    Returns:     A blessed TestCaseRun object hash

    Example:
    >>> TestCaseRun.get(1193)
    """
    return TestCaseRun.objects.get(**query).serialize()


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
def update(case_run_ids, values, **kwargs):
    """
    Description: Updates the fields of the selected case-runs.

    Params:      $caserun_ids - Integer/String/Array
                        Integer: A single TestCaseRun ID.
                        String:  A comma separates string of TestCaseRun IDs for batch
                                 processing.
                        Array:   An array of TestCaseRun IDs for batch mode processing

                 $values - Hash of keys matching TestCaseRun fields and the new values
                 to set each field to.
                         +--------------------+----------------+
                         | Field              | Type           |
                         +--------------------+----------------+
                         | build              | Integer        |
                         | assignee           | Integer        |
                         | case_run_status    | Integer        |
                         | notes              | String         |
                         | sortkey            | Integer        |
                         +--------------------+----------------+

    Returns:     Hash/Array: In the case of a single object, it is returned. If a
                 list was passed, it returns an array of object hashes. If the
                 update on any particular object failed, the hash will contain a
                 ERROR key and the message as to why it failed.

    Example:
    # Update alias to 'tcms' for case 12345 and 23456
    >>> TestCaseRun.update([12345, 23456], {'assignee': 2206})
    """
    from datetime import datetime
    from tcms.core import forms
    from tcms.testruns.forms import XMLRPCUpdateCaseRunForm

    pks_to_update = pre_process_ids(case_run_ids)

    tcrs = TestCaseRun.objects.filter(pk__in=pks_to_update)
    form = XMLRPCUpdateCaseRunForm(values)

    if form.is_valid():
        data = {}

        if form.cleaned_data['build']:
            data['build'] = form.cleaned_data['build']

        if form.cleaned_data['assignee']:
            data['assignee'] = form.cleaned_data['assignee']

        if form.cleaned_data['case_run_status']:
            data['case_run_status'] = form.cleaned_data['case_run_status']
            request = kwargs.get(REQUEST_KEY)
            data['tested_by'] = request.user
            data['close_date'] = datetime.now()

        if 'notes' in values:
            if values['notes'] in (None, ''):
                data['notes'] = values['notes']
            if form.cleaned_data['notes']:
                data['notes'] = form.cleaned_data['notes']

        if form.cleaned_data['sortkey'] is not None:
            data['sortkey'] = form.cleaned_data['sortkey']

        tcrs.update(**data)

    else:
        raise ValueError(forms.errors_to_list(form))

    query = {'pk__in': pks_to_update}
    return TestCaseRun.to_xmlrpc(query)


@rpc_method(name='TestCaseRun.attach_log')
def attach_log(case_run_id, name, url):
    """
    Description: Add new log link to TestCaseRun

    Params:     $caserun_id - Integer
                $name       - String: A short description to this new link, and accept
                                      64 characters at most.
                $url        - String: The actual URL.
    """
    test_case_run = TestCaseRun.objects.get(pk=case_run_id)
    create_link(name=name, url=url, link_to=test_case_run)


@rpc_method(name='TestCaseRun.dettach_log')
def detach_log(case_run_id, link_id):
    """
    Description: Remove log link to TestCaseRun

    Params:     $case_run_id - Integer
                $link_id     - Integer: Id of LinkReference instance
    """
    TestCaseRun.objects.get(pk=case_run_id)
    LinkReference.unlink(link_id)


@rpc_method(name='TestCaseRun.get_logs')
def get_logs(case_run_id):
    """
    Description:  Get log links to TestCaseRun

    Params:     $case_run_id - Integer:
    """
    test_case_run = TestCaseRun.objects.get(pk=case_run_id)
    links = LinkReference.get_from(test_case_run)
    s = XMLRPCSerializer(links)
    return s.serialize_queryset()
