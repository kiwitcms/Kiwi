# -*- coding: utf-8 -*-
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.management.models import Tag
from tcms.rpc.api.forms.testrun import UpdateForm, UserForm
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import TestCase
from tcms.testruns.forms import NewRunForm
from tcms.testruns.models import TestExecution, TestRun

__all__ = (
    'create',
    'update',
    'filter',

    'add_case',
    'get_cases',
    'remove_case',

    'add_tag',
    'remove_tag',

    'add_cc',
    'remove_cc',
)


@permissions_required('testruns.add_testexecution')
@rpc_method(name='TestRun.add_case')
def add_case(run_id, case_id):
    """
    .. function:: RPC TestRun.add_case(run_id, case_id)

        Add a TestCase to the selected test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param case_id: PK of TestCase to be added
        :type case_id: int
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :rtype: dict
        :raises DoesNotExist: if objects specified by the PKs don't exist
        :raises PermissionDenied: if missing *testruns.add_testexecution* permission
        :raises RuntimeError: if test case status is not CONFIRMED
    """
    run = TestRun.objects.get(pk=run_id)
    case = TestCase.objects.get(pk=case_id)

    if run.case_run.filter(case=case).exists():
        return run.case_run.filter(case=case).first().serialize()

    if not case.case_status.is_confirmed:
        raise RuntimeError("TC-%d status is not confirmed" % case.pk)

    # always add new TEs at the end of TR
    sortkey = 10
    last_te = run.case_run.order_by('sortkey').last()
    if last_te:  # in case there are no other TEs
        sortkey += last_te.sortkey

    execution = run.create_execution(case=case, sortkey=sortkey)
    return execution.serialize()


@permissions_required('testruns.delete_testexecution')
@rpc_method(name='TestRun.remove_case')
def remove_case(run_id, case_id):
    """
    .. function:: RPC TestRun.remove_case(run_id, case_id)

        Remove a TestCase from the selected test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param case_id: PK of TestCase to be removed
        :type case_id: int
        :raises PermissionDenied: if missing *testruns.delete_testexecution* permission
    """
    TestExecution.objects.filter(run=run_id, case=case_id).delete()


@permissions_required('testruns.view_testrun')
@rpc_method(name='TestRun.get_cases')
def get_cases(run_id):
    """
    .. function:: RPC TestRun.get_cases(run_id)

        Get the list of test cases that are attached to a test run.

        :param run_id: PK of TestRun to inspect
        :type run_id: int
        :return: Serialized list of :class:`tcms.testcases.models.TestCase` objects
                 augmented with ``execution_id`` and ``status`` information.
        :rtype: list(dict)
    """
    tcs_serializer = TestCase.to_xmlrpc(query={'case_run__run_id': run_id})

    qs = TestExecution.objects.filter(run_id=run_id).values(
        'case', 'pk', 'status__name')
    extra_info = dict(((row['case'], row) for row in qs.iterator()))

    for case in tcs_serializer:
        info = extra_info[case['id']]
        case['execution_id'] = info['pk']
        case['status'] = info['status__name']

    return tcs_serializer


@permissions_required('testruns.add_testruntag')
@rpc_method(name='TestRun.add_tag')
def add_tag(run_id, tag_name, **kwargs):
    """
    .. function:: RPC TestRun.add_tag(run_id, tag)

        Add one tag to the specified test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param tag_name: Tag name to add
        :type tag_name: str
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Serialized list of :class:`tcms.management.models.Tag` objects
        :rtype: dict
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
    .. function:: RPC TestRun.remove_tag(run_id, tag)

        Remove a tag from the specified test run.

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param tag_name: Tag name to add
        :type tag_name: str
        :return: Serialized list of :class:`tcms.management.models.Tag` objects
        :rtype: dict
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
    .. function:: RPC TestRun.create(values)

        Create new TestRun object and store it in the database.

        :param values: Field values for :class:`tcms.testruns.models.TestRun`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestRun` object
        :rtype: dict
        :raises PermissionDenied: if missing *testruns.add_testrun* permission
        :raises ValueError: if data validations fail

        Example::

            >>> values = {'build': 384,
                'manager': 137,
                'plan': 137,
                'summary': 'Testing XML-RPC for TCMS',
            }
            >>> TestRun.create(values)
    """
    form = NewRunForm(values)
    form.populate(values.get('plan'))

    if form.is_valid():
        test_run = form.save()
        return test_run.serialize()

    raise ValueError(form_errors_to_list(form))


@permissions_required('testruns.view_testrun')
@rpc_method(name='TestRun.filter')
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC TestRun.filter(query)

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
    .. function:: RPC TestRun.update(run_id, values)

        Update the selected TestRun

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param values: Field values for :class:`tcms.testruns.models.TestRun`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestRun` object
        :rtype: dict
        :raises PermissionDenied: if missing *testruns.change_testrun* permission
        :raises ValueError: if data validations fail
    """
    test_run = TestRun.objects.get(pk=run_id)
    form = UpdateForm(values, instance=test_run)

    if values.get('product'):
        form.populate(product_id=values['product'])

    if not form.is_valid():
        raise ValueError(form_errors_to_list(form))

    test_run = form.save()
    return test_run.serialize()


@permissions_required('testruns.change_testrun')
@rpc_method(name='TestRun.add_cc')
def add_cc(run_id, username):
    """
    .. function:: RPC TestRun.add_cc(run_id, username)

        Add the chosen user to TestRun CC

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param username: PK, email or username
        :type username: string
        :raises DoesNotExist: if test run specified by the PK doesn't exist
        :raises PermissionDenied: if missing *testruns.change_testrun* permission
        :raises ValueError: if data validations fail
    """
    test_run = TestRun.objects.get(pk=run_id)
    form = UserForm({'user': username})

    if not form.is_valid():
        raise ValueError(form_errors_to_list(form))

    test_run.add_cc(form.cleaned_data['user'])


@permissions_required('testruns.change_testrun')
@rpc_method(name='TestRun.remove_cc')
def remove_cc(run_id, username):
    """
    .. function:: RPC TestRun.remove_cc(run_id, username)

        Remove the chosen user from TestRun CC

        :param run_id: PK of TestRun to modify
        :type run_id: int
        :param username: PK, email or username
        :type username: string
        :raises DoesNotExist: if test run specified by the PK doesn't exist
        :raises PermissionDenied: if missing *testruns.change_testrun* permission
        :raises ValueError: if data validations fail
    """
    test_run = TestRun.objects.get(pk=run_id)
    form = UserForm({'user': username})

    if not form.is_valid():
        raise ValueError(form_errors_to_list(form))

    test_run.remove_cc(form.cleaned_data['user'])
