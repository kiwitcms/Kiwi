# -*- coding: utf-8 -*-
import time

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.core.utils import form_errors_to_list
from tcms.core.contrib.comments.forms import SimpleForm
from tcms.core.contrib.comments import utils as comment_utils
from tcms.core.contrib.linkreference.views import create_link
from tcms.core.contrib.linkreference.models import LinkReference
from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.testruns.models import TestCaseRun
from tcms.xmlrpc.decorators import permissions_required

__all__ = (
    'create',
    'update',
    'filter',

    'add_comment',

    'add_log',
    'get_logs',
    'remove_log',
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
    case_run = TestCaseRun.objects.get(pk=case_run_id)

    data = {
        'content_type': 'testruns.testcaserun',
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
        run = form.cleaned_data['run']

        testcase_run = run.add_case_run(
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
    return TestCaseRun.to_xmlrpc(values)


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
    serialier = XMLRPCSerializer(links)
    return serialier.serialize_queryset()
