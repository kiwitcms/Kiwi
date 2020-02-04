# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers import comments
from tcms.core.utils import form_errors_to_list
from tcms.issuetracker.kiwitcms import KiwiTCMS
from tcms.rpc.api.forms.testrun import NewExecutionForm, UpdateExecutionForm
from tcms.rpc.api.utils import tracker_from_url
from tcms.rpc.decorators import permissions_required
from tcms.rpc.serializer import Serializer
from tcms.testruns.models import TestExecution

__all__ = (
    'create',
    'update',
    'filter',

    'add_comment',
    'remove_comment',

    'add_link',
    'get_links',
    'remove_link',
)


@permissions_required('django_comments.add_comment')
@rpc_method(name='TestExecution.add_comment')
def add_comment(execution_id, comment, **kwargs):
    """
    .. function:: XML-RPC TestExecution.add_comment(execution_id, comment)

        Add comment to selected test execution.

        :param execution_id: PK of a TestExecution object
        :param execution_id: int
        :param comment: The text to add as a comment
        :param comment: str
        :return: None or JSON string in case of errors
        :raises: PermissionDenied if missing *django_comments.add_comment* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)
    comments.add_comment([execution], comment, kwargs.get(REQUEST_KEY).user)


@permissions_required('django_comments.delete_comment')
@rpc_method(name='TestExecution.remove_comment')
def remove_comment(execution_id, comment_id=None):
    """
    .. function:: TestExecution.remove_comment(execution_id, comment_id)

        Remove all or specified comment(s) from selected test execution.

        :param execution_id: PK of a TestExecution object
        :param execution_id: int
        :param comment_id: PK of a Comment object or None
        :param comment_id: int
        :return: None
        :raises: PermissionDenied if missing *django_comments.delete_comment* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)
    to_be_deleted = comments.get_comments(execution)
    if comment_id:
        to_be_deleted = to_be_deleted.filter(pk=comment_id)

    to_be_deleted.delete()


# todo: this is very similar, if not duplicate to TestRun.add_case IMO
# should we schedule it for removal ?!?
@permissions_required('testruns.add_testexecution')
@rpc_method(name='TestExecution.create')
def create(values):
    """
    .. function:: XML-RPC TestExecution.create(values)

        Create new TestExecution object and store it in the database.

        :param values: Field values for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :raises: PermissionDenied if missing *testruns.add_testexecution* permission

        Minimal parameters::

            >>> values = {
                'run': 1990,
                'case': 12345,
                'build': 123,
            }
            >>> TestExecution.create(values)
    """

    form = NewExecutionForm(values)

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


@rpc_method(name='TestExecution.filter')
def filter(values):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC TestExecution.filter(values)

        Perform a search and return the resulting list of test case executions.

        :param values: Field lookups for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :return: List of serialized :class:`tcms.testruns.models.TestExecution` objects
        :rtype: list(dict)
    """
    return TestExecution.to_xmlrpc(values)


@permissions_required('testruns.change_testexecution')
@rpc_method(name='TestExecution.update')
def update(execution_id, values, **kwargs):
    """
    .. function:: XML-RPC TestExecution.update(execution_id, values)

        Update the selected TestExecution

        :param execution_id: PK of TestExecution to modify
        :type execution_id: int
        :param values: Field values for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :raises: PermissionDenied if missing *testruns.change_testexecution* permission
    """

    tcr = TestExecution.objects.get(pk=execution_id)
    form = UpdateExecutionForm(values)

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

        if form.cleaned_data['tested_by']:
            tcr.tested_by = form.cleaned_data['tested_by']

        tcr.save()

    else:
        raise ValueError(form_errors_to_list(form))

    return tcr.serialize()


# todo: missing permissions
@rpc_method(name='TestExecution.add_link')
def add_link(values, update_tracker=False):
    """
    .. function:: XML-RPC TestExecution.add_link(values)

        Add new URL link to a TestExecution

        :param values: Field values for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type values: dict
        :param update_tracker: Automatically update Issue Tracker by placing a comment
                               linking back to the failed TestExecution.
        :type update_tracker: bool, default=False
        :return: Serialized
                 :class:`tcms.core.contrib.linkreference.models.LinkReference` object
        :raises: RuntimeError if operation not successfull

        .. note::

            Always 'link' with IT instance if URL is from Kiwi TCMS own bug tracker!
    """
    link, _ = LinkReference.objects.get_or_create(**values)
    response = model_to_dict(link)
    tracker = tracker_from_url(link.url)

    if (link.is_defect and
            update_tracker and
            not tracker.is_adding_testcase_to_issue_disabled()) or \
            isinstance(tracker, KiwiTCMS):
        tracker.add_testexecution_to_issue([link.execution], link.url)

    return response


# todo: missing permissions
@rpc_method(name='TestExecution.remove_link')
def remove_link(query):
    """
    .. function:: XML-RPC TestExecution.remove_link(query)

        Remove URL link from TestExecution

        :param query: Field lookups for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type query: dict
        :return: None
    """
    LinkReference.objects.filter(**query).delete()


@rpc_method(name='TestExecution.get_links')
def get_links(query):
    """
    .. function:: XML-RPC TestExecution.get_links(query)

        Get URL links for the specified TestExecution

        :param query: Field lookups for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type query: dict
        :return: Serialized list of :class:`tcms.core.contrib.linkreference.models.LinkReference`
                 objects
    """
    links = LinkReference.objects.filter(**query)
    serialier = Serializer(links)
    return serialier.serialize_queryset()
