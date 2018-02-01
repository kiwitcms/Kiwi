# -*- coding: utf-8 -*-
from datetime import datetime

from modernrpc.core import rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.management.models import TestTag, TCMSEnvValue
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestRun
from tcms.xmlrpc.utils import pre_process_estimated_time
from tcms.xmlrpc.utils import pre_process_ids
from tcms.xmlrpc.decorators import permissions_required
from tcms.testruns.forms import XMLRPCUpdateRunForm, XMLRPCNewRunForm


__all__ = (
    'add_case',
    'remove_case',
    'get_cases',

    'add_env_value',
    'remove_env_value',

    'create',
    'filter',
    'update',

    'add_tag',
    'remove_tag',

    'get_bugs',
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
def add_tag(run_id, tag):
    """
    .. function: XML-RPC TestRun.add_tag(run_id, tag)

        Add one tag to the specified test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param tag: Tag name to add
        :type tag: str
        :return: None
        :raises: PermissionDenied if missing *testruns.add_testruntag* permission
        :raises: TestRun.DoesNotExist if object specified by PK doesn't exist
    """
    t, _ = TestTag.objects.get_or_create(name=tag)
    TestRun.objects.get(pk=run_id).add_tag(t)


@permissions_required('testruns.delete_testruntag')
@rpc_method(name='TestRun.remove_tag')
def remove_tag(run_id, tag):
    """
    .. function: XML-RPC TestRun.remove_tag(run_id, tag)

        Remove a tag from the specified test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param tag: Tag name to add
        :type tag: str
        :return: None
        :raises: PermissionDenied if missing *testruns.delete_testruntag* permission
        :raises: DoesNotExist if objects specified don't exist
    """
    t = TestTag.objects.get(name=tag)
    TestRun.objects.get(pk=run_id).remove_tag(t)


@permissions_required('testruns.add_testrun')
@rpc_method(name='TestRun.create')
def create(values):
    """
    .. function:: XML-RPC TestRun.create(values)

        Create new TestRun object and store it in the database.

        :param values: Field values for :class:`tcms.testruns.models.TestRun`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestRun` object
        :raises: PermissionDenied if missing *testruns.add_testrun* permission
        :raises: ValueError if data validations fail

        Example::

            >>> values = {'build': 384,
                'manager': 137,
                'plan': 137,
                'product': 61,
                'product_version': 93,
                'summary': 'Testing XML-RPC for TCMS',
            }
            >>> TestRun.create(values)
    """
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


@permissions_required('testruns.change_testrun')
@rpc_method(name='TestRun.update')
def update(run_id, values):
    """
    .. function:: XML-RPC TestRun.update(run_id, values)

        Update the selected TestRun

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param values: Field values for :class:`tcms.testruns.models.TestRun`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestRun` object
        :raises: PermissionDenied if missing *testruns.change_testrun* permission
        :raises: ValueError if data validations fail
    """
    if (values.get('product_version') and not values.get('product')):
        raise ValueError('Field "product" is required by product_version')

    if values.get('estimated_time'):
        values['estimated_time'] = pre_process_estimated_time(
            values.get('estimated_time'))

    form = XMLRPCUpdateRunForm(values)
    if values.get('product_version'):
        form.populate(product_id=values['product'])

    if form.is_valid():
        tr = TestRun.objects.get(pk=run_id)
        if form.cleaned_data['plan']:
            tr.plan = form.cleaned_data['plan']

        if form.cleaned_data['build']:
            tr.build = form.cleaned_data['build']

        if form.cleaned_data['manager']:
            tr.manager = form.cleaned_data['manager']

        if 'default_tester' in values:
            if values.get('default_tester') and \
                    form.cleaned_data['default_tester']:
                tr.default_tester = form.cleaned_data['default_tester']
            else:
                tr.default_tester = None

        if form.cleaned_data['summary']:
            tr.summary = form.cleaned_data['summary']

        if values.get('estimated_time') is not None:
            tr.estimated_time = form.cleaned_data['estimated_time']

        if form.cleaned_data['product_version']:
            tr.product_version = form.cleaned_data['product_version']

        if 'notes' in values:
            if values['notes'] in (None, ''):
                tr.notes = values['notes']
            if form.cleaned_data['notes']:
                tr.notes = form.cleaned_data['notes']

        if form.cleaned_data['plan_text_version']:
            tr.plan_text_version = form.cleaned_data['plan_text_version']

        if isinstance(form.cleaned_data['status'], int):
            if form.cleaned_data['status']:
                tr.stop_date = datetime.now()
            else:
                tr.stop_date = None

        tr.save()
    else:
        raise ValueError(form_errors_to_list(form))

    return tr.serialize()


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
