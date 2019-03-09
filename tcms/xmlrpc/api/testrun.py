# -*- coding: utf-8 -*-
from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.core.utils import form_errors_to_list
from tcms.management.models import Tag
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestExecution
from tcms.testruns.models import TestRun
from tcms.xmlrpc.decorators import permissions_required
from tcms.testruns.forms import XMLRPCUpdateRunForm, XMLRPCNewRunForm


__all__ = (
    'create',
    'update',
    'filter',

    'add_case',
    'get_cases',
    'remove_case',

    'add_tag',
    'remove_tag',
)


@permissions_required('testruns.add_testexecution')
@rpc_method(name='TestRun.add_case')
def add_case(run_id, case_id):
    """
    .. function:: XML-RPC TestRun.add_case(run_id, case_id)

        Add a TestCase to the selected test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param case_id: PK of TestCase to be added
        :type case_id: int
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :raises: DoesNotExist if objects specified by the PKs don't exist
        :raises: PermissionDenied if missing *testruns.add_testexecution* permission
    """
    test_case_run = TestRun.objects.get(pk=run_id).add_case_run(
        case=TestCase.objects.get(pk=case_id)
    )
    return test_case_run.serialize()


@permissions_required('testruns.delete_testexecution')
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
        :raises: PermissionDenied if missing *testruns.delete_testexecution* permission
    """
    TestExecution.objects.filter(run=run_id, case=case_id).delete()


@rpc_method(name='TestRun.get_cases')
def get_cases(run_id):
    """
    .. function:: XML-RPC TestRun.get_cases(run_id)

        Get the list of test cases that are attached to a test run.

        :param run_id: PK of TestRun to inspect
        :type run_id: int
        :return: Serialized list of :class:`tcms.testcases.models.TestCase` objects
                 augmented with ``case_run_id`` and ``status`` information.
        :rtype: list(dict)
    """
    tcs_serializer = TestCase.to_xmlrpc(query={'case_run__run_id': run_id})

    qs = TestExecution.objects.filter(run_id=run_id).values(
        'case', 'pk', 'status__name')
    extra_info = dict(((row['case'], row) for row in qs.iterator()))

    for case in tcs_serializer:
        info = extra_info[case['case_id']]
        case['case_run_id'] = info['pk']
        case['status'] = info['status__name']

    return tcs_serializer


@permissions_required('testruns.add_testruntag')
@rpc_method(name='TestRun.add_tag')
def add_tag(run_id, tag_name, **kwargs):
    """
    .. function:: XML-RPC TestRun.add_tag(run_id, tag)

        Add one tag to the specified test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param tag_name: Tag name to add
        :type tag_name: str
        :return: Serialized list of :class:`tcms.management.models.Tag` objects
        :raises: PermissionDenied if missing *testruns.add_testruntag* permission
        :raises: TestRun.DoesNotExist if object specified by PK doesn't exist
        :raises: Tag.DoesNotExist if missing *management.add_tag* permission and *tag_name*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag, _ = Tag.get_or_create(request.user, tag_name)
    test_run = TestRun.objects.get(pk=run_id)
    test_run.add_tag(tag)
    return Tag.to_xmlrpc({'pk__in': test_run.tag.all()})


@permissions_required('testruns.delete_testruntag')
@rpc_method(name='TestRun.remove_tag')
def remove_tag(run_id, tag_name):
    """
    .. function:: XML-RPC TestRun.remove_tag(run_id, tag)

        Remove a tag from the specified test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param tag_name: Tag name to add
        :type tag_name: str
        :return: Serialized list of :class:`tcms.management.models.Tag` objects
        :raises: PermissionDenied if missing *testruns.delete_testruntag* permission
        :raises: DoesNotExist if objects specified don't exist
    """
    tag = Tag.objects.get(name=tag_name)
    test_run = TestRun.objects.get(pk=run_id)
    test_run.remove_tag(tag)
    return Tag.to_xmlrpc({'pk__in': test_run.tag.all()})


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
                'summary': 'Testing XML-RPC for TCMS',
            }
            >>> TestRun.create(values)
    """
    form = XMLRPCNewRunForm(values)
    form.assign_plan(values.get('plan'))

    if form.is_valid():
        test_run = TestRun.objects.create(
            product_version=form.cleaned_data['plan'].product_version,
            summary=form.cleaned_data['summary'],
            notes=form.cleaned_data['notes'],
            plan=form.cleaned_data['plan'],
            build=form.cleaned_data['build'],
            manager=form.cleaned_data['manager'],
            default_tester=form.cleaned_data['default_tester'],
        )
    else:
        raise ValueError(form_errors_to_list(form))

    return test_run.serialize()


@rpc_method(name='TestRun.filter')
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC TestRun.filter(query)

        Perform a search and return the resulting list of test runs.

        :param query: Field lookups for :class:`tcms.testruns.models.TestRun`
        :type query: dict
        :return: List of serialized :class:`tcms.testruns.models.TestRun` objects
        :rtype: list(dict)
    """

    if query is None:
        query = {}

    return TestRun.to_xmlrpc(query)


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
    if values.get('product_version') and not values.get('product'):
        raise ValueError('Field "product" is required by product_version')

    form = XMLRPCUpdateRunForm(values)
    if values.get('product_version'):
        form.populate(product_id=values['product'])

    if not form.is_valid():
        raise ValueError(form_errors_to_list(form))

    test_run = TestRun.objects.get(pk=run_id)
    if form.cleaned_data['plan']:
        test_run.plan = form.cleaned_data['plan']

    if form.cleaned_data['build']:
        test_run.build = form.cleaned_data['build']

    if form.cleaned_data['manager']:
        test_run.manager = form.cleaned_data['manager']

    test_run.default_tester = None

    if form.cleaned_data['default_tester']:
        test_run.default_tester = form.cleaned_data['default_tester']

    if form.cleaned_data['summary']:
        test_run.summary = form.cleaned_data['summary']

    if form.cleaned_data['product_version']:
        test_run.product_version = form.cleaned_data['product_version']

    if 'notes' in values:
        if values['notes'] in (None, ''):
            test_run.notes = values['notes']
        if form.cleaned_data['notes']:
            test_run.notes = form.cleaned_data['notes']

    if form.cleaned_data['stop_date']:
        test_run.stop_date = form.cleaned_data['stop_date']

    test_run.save()
    return test_run.serialize()
