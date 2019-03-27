# -*- coding: utf-8 -*-
import time

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.core.utils import form_errors_to_list
from tcms.core.contrib.comments.forms import SimpleForm
from tcms.core.contrib.comments import utils as comment_utils
from tcms.core.contrib.linkreference.views import create_link
from tcms.core.contrib.linkreference.models import LinkReference
from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.testruns.models import TestExecution
from tcms.xmlrpc.decorators import permissions_required

__all__ = (
    'create',
    'update',
    'filter',

    'add_comment',

    'add_link',
    'get_links',
    'remove_link',
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
        :return: None or JSON string in case of errors
    """
    case_run = TestExecution.objects.get(pk=case_run_id)

    data = {
        'content_type': 'testruns.testexecution',
        'object_pk': str(case_run_id),
        'timestamp': str(time.time()).split('.')[0],
    }
    data['security_hash'] = SimpleForm(case_run).generate_security_hash(**data)
    data['comment'] = comment

    form, _ = comment_utils.add_comment(kwargs.get(REQUEST_KEY), data)

    if not form.is_valid():
        return form.errors.as_json()

    return None


# todo: this is very similar, if not duplicate to TestRun.add_case IMO
# should we schedule it for removal ?!?
@permissions_required('testruns.add_testexecution')
@rpc_method(name='TestCaseRun.create')
def create(values):
    """
    .. function:: XML-RPC TestCaseRun.create(values)

        Create new TestCaseRun object and store it in the database.

        :param values: Field values for :class:`tcms.testruns.models.TestCaseRun`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestCaseRun` object
        :raises: PermissionDenied if missing *testruns.add_testexecution* permission

        Minimal parameters::

            >>> values = {
                'run': 1990,
                'case': 12345,
                'build': 123,
            }
            >>> TestExecution.create(values)
    """
    from tcms.testruns.forms import XMLRPCNewCaseRunForm

    form = XMLRPCNewCaseRunForm(values)

    if not isinstance(values, dict):
        raise TypeError('Argument values must be in dict type.')
    if not values:
        raise ValueError('Argument values is empty.')

    if form.is_valid():
        run = form.cleaned_data['run']

        testcase_run = run.add_case_run(
            case=form.cleaned_data['case'],
            build=form.cleaned_data['build'],
            assignee=form.cleaned_data['assignee'],
            status=form.cleaned_data['status'],
            case_text_version=form.cleaned_data['case_text_version'],
            sortkey=form.cleaned_data['sortkey']
        )
    else:
        raise ValueError(form_errors_to_list(form))

    return testcase_run.serialize()


@rpc_method(name='TestCaseRun.filter')
def filter(values):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC TestCaseRun.filter(values)

        Perform a search and return the resulting list of test case executions.

        :param values: Field lookups for :class:`tcms.testruns.models.TestCaseRun`
        :type values: dict
        :return: List of serialized :class:`tcms.testruns.models.TestCaseRun` objects
        :rtype: list(dict)
    """
    return TestExecution.to_xmlrpc(values)


@permissions_required('testruns.change_testexecution')
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
        :raises: PermissionDenied if missing *testruns.change_testexecution* permission
    """
    from tcms.testruns.forms import XMLRPCUpdateCaseRunForm

    tcr = TestExecution.objects.get(pk=case_run_id)
    form = XMLRPCUpdateCaseRunForm(values)

    if form.is_valid():
        if form.cleaned_data['build']:
            tcr.build = form.cleaned_data['build']

        if form.cleaned_data['assignee']:
            tcr.assignee = form.cleaned_data['assignee']

        if form.cleaned_data['status']:
            tcr.status = form.cleaned_data['status']
            request = kwargs.get(REQUEST_KEY)
            tcr.tested_by = request.user

        if form.cleaned_data['sortkey'] is not None:
            tcr.sortkey = form.cleaned_data['sortkey']

        tcr.save()

    else:
        raise ValueError(form_errors_to_list(form))

    return tcr.serialize()


@rpc_method(name='TestCaseRun.add_link')
def add_link(case_run_id, name, url):
    """
    .. function:: XML-RPC TestCaseRun.add_link(case_run_id, name, url)

        Add new URL link to a TestCaseRun

        :param case_run_id: PK of a TestCaseRun object
        :type case_run_id: int
        :param name: Name/description of the link
        :type name: str
        :param url: URL address
        :type url: str
        :return: ID of created link
        :rtype: int
        :raises: RuntimeError if operation not successfull
    """
    result = create_link({
        'name': name,
        'url': url,
        'target': 'TestExecution',
        'target_id': case_run_id
    })
    if result['rc'] != 0:
        raise RuntimeError(result['response'])
    return result['data']['pk']


@rpc_method(name='TestCaseRun.remove_link')
def remove_link(case_run_id, link_id):
    """
    .. function:: XML-RPC TestCaseRun.remove_link(case_run_id, link_id)

        Remove URL link from TestCaseRun

        :param case_run_id: PK of TestCaseRun to modify
        :type case_run_id: int
        :param link_id: PK of link to remove
        :type link_id: int
        :return: None
    """
    LinkReference.objects.filter(pk=link_id, test_case_run=case_run_id).delete()


@rpc_method(name='TestCaseRun.get_links')
def get_links(case_run_id):
    """
    .. function:: XML-RPC TestCaseRun.get_links(case_run_id)

        Get URL links for the specified TestCaseRun

        :param case_run_id: PK of TestCaseRun object
        :type case_run_id: int
        :return: Serialized list of :class:`tcms.core.contrib.linkreference.models.LinkReference`
                 objects
    """
    links = LinkReference.objects.filter(test_case_run=case_run_id)
    serialier = XMLRPCSerializer(links)
    return serialier.serialize_queryset()


# workaround for keeping backward-compatibility with users of the API calling TestCaseRun.*
@rpc_method(name='TestExecution.add_comment')
def test_execution_add_comment(case_run_id, comment, **kwargs):
    return add_comment(case_run_id, comment, **kwargs)


@permissions_required('testruns.add_testexecution')
@rpc_method(name='TestExecution.create')
def test_execution_create(values):
    return create(values)


@rpc_method(name='TestExecution.filter')
def test_execution_filter(values):
    return filter(values)


@rpc_method(name='TestExecution.get_links')
def test_execution_get_links(case_run_id):
    return get_links(case_run_id)


@rpc_method(name='TestExecution.remove_link')
def test_execution_remove_link(case_run_id, link_id):
    return remove_link(case_run_id, link_id)


@permissions_required('testruns.change_testexecution')
@rpc_method(name='TestExecution.update')
def test_execution_update(case_run_id, values, **kwargs):
    return update(case_run_id, values, **kwargs)


@rpc_method(name='TestExecution.add_link')
def test_execution_add_link(case_run_id, name, url):
    return add_link(case_run_id, name, url)
