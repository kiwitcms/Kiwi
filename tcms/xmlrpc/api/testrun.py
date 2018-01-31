# -*- coding: utf-8 -*-
from datetime import datetime

from modernrpc.core import rpc_method

from tcms.core.utils import string_to_list, form_errors_to_list
from tcms.management.models import TestTag, TCMSEnvValue
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestRun
from tcms.xmlrpc.utils import pre_process_estimated_time
from tcms.xmlrpc.utils import pre_process_ids
from tcms.xmlrpc.decorators import permissions_required

__all__ = (
    'add_case',
    'remove_case',
    'get_cases',

    'add_env_value',
    'remove_env_value',

    'filter',

    'add_tag',
    'create',
    'get_bugs',
    'get_tags',
    'remove_tag',
    'update',
)


@permissions_required('testruns.add_testcaserun')
@rpc_method(name='TestRun.add_case')
def add_case(run_id, case_id):
    """
    .. function:: XML-RPC TestRun.add_case(run_id, case_id)

        Add a TestCase to the selected test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param case_id: PK of TestCase to be added
        :type case_id: int
        :return: None
        :raises: DoesNotExist if objects specified by the PKs don't exist
        :raises: PermissionDenied if missing *testruns.add_testcaserun* permission
    """
    TestRun.objects.get(pk=run_id).add_case_run(
        case=TestCase.objects.get(pk=case_id)
    )


@permissions_required('testruns.delete_testcaserun')
@rpc_method(name='TestRun.remove_case')
def remove_case(run_id, case_id):
    """
    .. function:: XML-RPC TestRun.remove_case(run_id, case_id)

        Remove a TestCase from the selected test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param case_id: PK of TestCase to be removed
        :type case_id: int
        :return: None
        :raises: PermissionDenied if missing *testruns.delete_testcaserun* permission
    """
    TestCaseRun.objects.filter(run=run_id, case=case_id).delete()


@rpc_method(name='TestRun.get_cases')
def get_cases(run_id):
    """
    .. function:: XML-RPC TestRun.get_cases(run_id)

        Get the list of test cases that are attached to a test run.

        :param run_id: PK of TestRun to inspect
        :type run_id: int
        :return: Serialized list of :class:`tcms.testcases.models.TestCase` objects
                 augmented with ``case_run_id`` and ``case_run_status`` information.
        :rtype: list(dict)
    """
    tcs_serializer = TestCase.to_xmlrpc(query={'case_run__run_id': run_id})

    qs = TestCaseRun.objects.filter(run_id=run_id).values(
        'case', 'pk', 'case_run_status__name')
    extra_info = dict(((row['case'], row) for row in qs.iterator()))

    for case in tcs_serializer:
        info = extra_info[case['case_id']]
        case['case_run_id'] = info['pk']
        case['case_run_status'] = info['case_run_status__name']

    return tcs_serializer


@permissions_required('testruns.add_testruntag')
@rpc_method(name='TestRun.add_tag')
def add_tag(run_ids, tags):
    """
    Description: Add one or more tags to the selected test runs.

    Params:      $run_ids - Integer/Array/String: An integer representing the ID in the database,
                                                  an arry of run_ids, or a string of
                                                  comma separated run_ids.

                 $tags - String/Array - A single tag, an array of tags,
                                        or a comma separated list of tags.

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occured.

    Example:
    # Add tag 'foobar' to run 1234
    >>> TestPlan.add_tag(1234, 'foobar')
    # Add tag list ['foo', 'bar'] to run list [12345, 67890]
    >>> TestPlan.add_tag([12345, 67890], ['foo', 'bar'])
    # Add tag list ['foo', 'bar'] to run list [12345, 67890] with String
    >>> TestPlan.add_tag('12345, 67890', 'foo, bar')
    """
    trs = TestRun.objects.filter(pk__in=pre_process_ids(value=run_ids))
    if not isinstance(tags, str) and not isinstance(tags, list):
        raise ValueError('Parameter tags must be a string or list(string)')
    tags = string_to_list(tags)

    for tag in tags:
        t, c = TestTag.objects.get_or_create(name=tag)
        for tr in trs.iterator():
            tr.add_tag(tag=t)

    return


@permissions_required('testruns.add_testrun')
@rpc_method(name='TestRun.create')
def create(values):
    """
    Description: Creates a new Test Run object and stores it in the database.

    Params:      $values - Hash: A reference to a hash with keys and values
                           matching the fields of the test run to be created.
      +-------------------+----------------+-----------+---------------------------------------+
      | Field             | Type           | Null      | Description                           |
      +-------------------+----------------+-----------+---------------------------------------+
      | plan              | Integer        | Required  | ID of test plan                       |
      | build             | Integer/String | Required  | ID of Build                           |
      | manager           | Integer        | Required  | ID of run manager                     |
      | summary           | String         | Required  |                                       |
      | product           | Integer        | Required  | ID of product                         |
      | product_version   | Integer        | Required  | ID of product version                 |
      | default_tester    | Integer        | Optional  | ID of run default tester              |
      | plan_text_version | Integer        | Optional  |                                       |
      | estimated_time    | String         | Optional  | 2h30m30s(recommend) or HH:MM:SS Format|
      | notes             | String         | Optional  |                                       |
      | status            | Integer        | Optional  | 0:RUNNING 1:STOPPED  (default 0)      |
      | case              | Array/String   | Optional  | list of case ids to add to the run    |
      | tag               | Array/String   | Optional  | list of tag to add to the run         |
      +-------------------+----------------+-----------+---------------------------------------+

    Returns:     The newly created object hash.

    Example:
    >>> values = {'build': 384,
        'manager': 137,
        'plan': 137,
        'product': 61,
        'product_version': 93,
        'summary': 'Testing XML-RPC for TCMS',
    }
    >>> TestRun.create(values)
    """
    from tcms.testruns.forms import XMLRPCNewRunForm

    if not values.get('product'):
        raise ValueError('Value of product is required')
    # TODO: XMLRPC only accept HH:MM:SS rather than DdHhMm

    if values.get('estimated_time'):
        values['estimated_time'] = pre_process_estimated_time(
            values.get('estimated_time'))

    if values.get('case'):
        values['case'] = pre_process_ids(value=values['case'])

    form = XMLRPCNewRunForm(values)
    form.populate(product_id=values['product'])

    if form.is_valid():
        tr = TestRun.objects.create(
            product_version=form.cleaned_data['product_version'],
            plan_text_version=form.cleaned_data['plan_text_version'],
            stop_date=form.cleaned_data['status'] and datetime.now() or None,
            summary=form.cleaned_data['summary'],
            notes=form.cleaned_data['notes'],
            estimated_time=form.cleaned_data['estimated_time'],
            plan=form.cleaned_data['plan'],
            build=form.cleaned_data['build'],
            manager=form.cleaned_data['manager'],
            default_tester=form.cleaned_data['default_tester'],
        )

        if form.cleaned_data['case']:
            for c in form.cleaned_data['case']:
                tr.add_case_run(case=c)
                del c

        if form.cleaned_data['tag']:
            tags = form.cleaned_data['tag']
            if isinstance(tags, str):
                tags = [c.strip() for c in tags.split(',') if c]

            for tag in tags:
                t, c = TestTag.objects.get_or_create(name=tag)
                tr.add_tag(tag=t)
                del tag, t, c
    else:
        raise ValueError(form_errors_to_list(form))

    return tr.serialize()


@rpc_method(name='TestRun.filter')
def filter(query={}):
    """
    .. function:: XML-RPC TestRun.filter(query)

        Perform a search and return the resulting list of test runs.

        :param query: Field lookups for :class:`tcms.testruns.models.TestRun`
        :type query: dict
        :return: List of serialized :class:`tcms.testruns.models.TestRun` objects
        :rtype: list(dict)
    """
    return TestRun.to_xmlrpc(query)


@rpc_method(name='TestRun.get_bugs')
def get_bugs(run_ids):
    """
    *** FIXME: BUGGY IN SERIALISER - List can not be serialize. ***
    Description: Get the list of bugs attached to this run.

    Params:      $run_ids - Integer/Array/String: An integer representing the ID in the database
                                                  an array of integers or a comma separated list
                                                  of integers.

    Returns:     Array: An array of bug object hashes.

    Example:
    # Get bugs belong to ID 12345
    >>> TestRun.get_bugs(12345)
    # Get bug belong to run ids list [12456, 23456]
    >>> TestRun.get_bugs([12456, 23456])
    # Get bug belong to run ids list 12456 and 23456 with string
    >>> TestRun.get_bugs('12456, 23456')
    """
    from tcms.testcases.models import TestCaseBug

    trs = TestRun.objects.filter(
        run_id__in=pre_process_ids(value=run_ids)
    )
    tcrs = TestCaseRun.objects.filter(
        run__run_id__in=trs.values_list('run_id', flat=True)
    )

    query = {'case_run__case_run_id__in': tcrs.values_list('case_run_id',
                                                           flat=True)}
    return TestCaseBug.to_xmlrpc(query)


@rpc_method(name='TestRun.get_tags')
def get_tags(run_id):
    """
    Description: Get the list of tags attached to this run.

    Params:      $run_id - Integer: An integer representing the ID of the run in the database

    Returns:     Array: An array of tag object hashes.

    Example:
    >>> TestRun.get_tags(1193)
    """
    test_run = TestRun.objects.get(run_id=run_id)

    tag_ids = test_run.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    return TestTag.to_xmlrpc(query)


@permissions_required('testruns.delete_testruntag')
@rpc_method(name='TestRun.remove_tag')
def remove_tag(run_ids, tags):
    """
    Description: Remove a tag from a run.

    Params:      $run_ids - Integer/Array/String: An integer or alias representing the ID in the
                             database, an array of run_ids, or a string of comma separated run_ids.

                 $tag - String - A single tag to be removed.

    Returns:     Array: Empty on success.

    Example:
    # Remove tag 'foo' from run 1234
    >>> TestRun.remove_tag(1234, 'foo')
    # Remove tag 'foo' and 'bar' from run list [56789, 12345]
    >>> TestRun.remove_tag([56789, 12345], ['foo', 'bar'])
    # Remove tag 'foo' and 'bar' from run list '56789, 12345' with String
    >>> TestRun.remove_tag('56789, 12345', 'foo, bar')
    """
    test_runs = TestRun.objects.filter(
        run_id__in=pre_process_ids(value=run_ids)
    )

    if not isinstance(tags, str) and not isinstance(tags, list):
        raise ValueError('Parameter tags must be a string or list(string)')

    test_tags = TestTag.objects.filter(
        name__in=string_to_list(tags)
    )

    for test_run in test_runs.iterator():
        for test_tag in test_tags.iterator():
            test_run.remove_tag(tag=test_tag)

    return


@permissions_required('testruns.change_testrun')
@rpc_method(name='TestRun.update')
def update(run_ids, values):
    """
    Description: Updates the fields of the selected test run.

    Params:      $run_ids - Integer/Array/String: An integer or alias representing the ID in the
                             database, an array of run_ids, or a string of comma separated run_ids.

                 $values - Hash of keys matching TestRun fields and the new values
                           to set each field to. See params of TestRun.create for description
    +-------------------+----------------+--------------------------------+
    | Field             | Type           | Description                    |
    +-------------------+----------------+--------------------------------+
    | plan              | Integer        | TestPlan.plan_id               |
    | product           | Integer        | Product.id                     |
    | build             | Integer        | Build.id                       |
    | manager           | Integer        | Auth.User.id                   |
    | default_tester    | Intege         | Auth.User.id                   |
    | summary           | String         |                                |
    | estimated_time    | TimeDelta      | 2h30m30s(recommend) or HH:MM:SS|
    | product_version   | Integer        |                                |
    | plan_text_version | Integer        |                                |
    | notes             | String         |                                |
    | status            | Integer        | 0:RUNNING 1:FINISHED           |
    +-------------------+----------------+ -------------------------------+
    Returns:     Hash: The updated test run object.

    Example:
    # Update status to finished for run 1193 and 1194
    >>> TestRun.update([1193, 1194], {'status': 1})
    """
    from tcms.testruns.forms import XMLRPCUpdateRunForm

    if (values.get('product_version') and not values.get('product')):
        raise ValueError('Field "product" is required by product_version')

    if values.get('estimated_time'):
        values['estimated_time'] = pre_process_estimated_time(
            values.get('estimated_time'))

    form = XMLRPCUpdateRunForm(values)
    if values.get('product_version'):
        form.populate(product_id=values['product'])

    if form.is_valid():
        trs = TestRun.objects.filter(pk__in=pre_process_ids(value=run_ids))
        _values = dict()
        if form.cleaned_data['plan']:
            _values['plan'] = form.cleaned_data['plan']

        if form.cleaned_data['build']:
            _values['build'] = form.cleaned_data['build']

        if form.cleaned_data['manager']:
            _values['manager'] = form.cleaned_data['manager']

        if 'default_tester' in values:
            if values.get('default_tester') and \
                    form.cleaned_data['default_tester']:
                _values['default_tester'] = form.cleaned_data['default_tester']
            else:
                _values['default_tester'] = None

        if form.cleaned_data['summary']:
            _values['summary'] = form.cleaned_data['summary']

        if values.get('estimated_time') is not None:
            _values['estimated_time'] = form.cleaned_data['estimated_time']

        if form.cleaned_data['product_version']:
            _values['product_version'] = form.cleaned_data['product_version']

        if 'notes' in values:
            if values['notes'] in (None, ''):
                _values['notes'] = values['notes']
            if form.cleaned_data['notes']:
                _values['notes'] = form.cleaned_data['notes']

        if form.cleaned_data['plan_text_version']:
            _values['plan_text_version'] = form.cleaned_data[
                'plan_text_version']

        if isinstance(form.cleaned_data['status'], int):
            if form.cleaned_data['status']:
                _values['stop_date'] = datetime.now()
            else:
                _values['stop_date'] = None

        trs.update(**_values)
    else:
        raise ValueError(form_errors_to_list(form))

    query = {'pk__in': trs.values_list('pk', flat=True)}
    return TestRun.to_xmlrpc(query)


@permissions_required('testruns.add_tcmsenvrunvaluemap')
@rpc_method(name='TestRun.add_env_value')
def add_env_value(run_id, env_value_id):
    """
    .. function:: XML-RPC TestRun.add_env_value(run_id, env_value_id)

        Add environment values to the given TestRun.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param env_value_id: PK of :class:`tcms.management.models.TCMSEnvValue`
                             object to add
        :type env_value_id: int
        :return: None
        :raises: PermissionDenied if missing *testruns.add_tcmsenvrunvaluemap* permission
        :raises: DoesNotExist if objects specified by PKs don't exist
    """
    TestRun.objects.get(pk=run_id).add_env_value(
        TCMSEnvValue.objects.get(pk=env_value_id)
    )


@permissions_required('testruns.delete_tcmsenvrunvaluemap')
@rpc_method(name='TestRun.remove_env_value')
def remove_env_value(run_id, env_value_id):
    """
    .. function:: XML-RPC TestRun.remove_env_value(run_id, env_value_id)

        Remove environment value from the given TestRun.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param env_value_id: PK of :class:`tcms.management.models.TCMSEnvValue`
                             object to be removed
        :type env_value_id: int
        :return: None
        :raises: PermissionDenied if missing *testruns.delete_tcmsenvrunvaluemap* permission
    """
    TestRun.objects.get(pk=run_id).remove_env_value(
        TCMSEnvValue.objects.get(pk=env_value_id)
    )
