# -*- coding: utf-8 -*-

from django.conf import settings
from django.forms.models import model_to_dict
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers import comments
from tcms.core.utils import form_errors_to_list
from tcms.rpc.api.forms.testrun import UpdateExecutionForm
from tcms.rpc.api.utils import tracker_from_url
from tcms.rpc.decorators import permissions_required
from tcms.rpc.serializer import Serializer
from tcms.testruns.models import TestExecution

# conditional import b/c this App can be disabled
if 'tcms.bugs.apps.AppConfig' in settings.INSTALLED_APPS:
    from tcms.issuetracker.kiwitcms import KiwiTCMS
else:
    class KiwiTCMS:  # pylint: disable=remove-empty-class,nested-class-found,too-few-public-methods
        pass


__all__ = (
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
    .. function:: RPC TestExecution.add_comment(execution_id, comment)

        Add comment to selected test execution.

        :param execution_id: PK of a TestExecution object
        :type execution_id: int
        :param comment: The text to add as a comment
        :type comment: str
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: dict
        :raises PermissionDenied: if missing *django_comments.add_comment* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)
    created = comments.add_comment([execution], comment, kwargs.get(REQUEST_KEY).user)
    # we always create only one comment
    return model_to_dict(created[0])


@permissions_required('django_comments.delete_comment')
@rpc_method(name='TestExecution.remove_comment')
def remove_comment(execution_id, comment_id=None):
    """
    .. function:: TestExecution.remove_comment(execution_id, comment_id)

        Remove all or specified comment(s) from selected test execution.

        :param execution_id: PK of a TestExecution object
        :type execution_id: int
        :param comment_id: PK of a Comment object or None
        :type comment_id: int
        :raises PermissionDenied: if missing *django_comments.delete_comment* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)
    to_be_deleted = comments.get_comments(execution)
    if comment_id:
        to_be_deleted = to_be_deleted.filter(pk=comment_id)

    to_be_deleted.delete()


@permissions_required('testruns.view_testexecution')
@rpc_method(name='TestExecution.filter')
def filter(values):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC TestExecution.filter(values)

        Perform a search and return the resulting list of test case executions.

        :param values: Field lookups for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :return: List of serialized :class:`tcms.testruns.models.TestExecution` objects
        :rtype: list(dict)
    """
    return TestExecution.to_xmlrpc(values)


@permissions_required('testruns.change_testexecution')
@rpc_method(name='TestExecution.update')
def update(execution_id, values):
    """
    .. function:: RPC TestExecution.update(execution_id, values)

        Update the selected TestExecution

        :param execution_id: PK of TestExecution to modify
        :type execution_id: int
        :param values: Field values for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :rtype: dict
        :raises ValueError: if data validations fail
        :raises PermissionDenied: if missing *testruns.change_testexecution* permission
    """
    test_execution = TestExecution.objects.get(pk=execution_id)

    if values.get('case_text_version') == 'latest':
        values['case_text_version'] = test_execution.case.history.latest().history_id

    form = UpdateExecutionForm(values, instance=test_execution)

    if form.is_valid():
        test_execution = form.save()
    else:
        raise ValueError(form_errors_to_list(form))

    return test_execution.serialize()


@permissions_required('linkreference.add_linkreference')
@rpc_method(name='TestExecution.add_link')
def add_link(values, update_tracker=False, **kwargs):
    """
    .. function:: RPC TestExecution.add_link(values)

        Add new URL link to a TestExecution

        :param values: Field values for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type values: dict
        :param update_tracker: Automatically update Issue Tracker by placing a comment
                               linking back to the failed TestExecution.
        :type update_tracker: bool, default=False
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Serialized
                 :class:`tcms.core.contrib.linkreference.models.LinkReference` object
        :rtype: dict
        :raises RuntimeError: if operation not successfull

        .. note::

            Always 'link' with IT instance if URL is from Kiwi TCMS own bug tracker!
    """
    link, _ = LinkReference.objects.get_or_create(**values)
    response = model_to_dict(link)
    request = kwargs.get(REQUEST_KEY)
    tracker = tracker_from_url(link.url, request)

    if (link.is_defect and
            update_tracker and
            not tracker.is_adding_testcase_to_issue_disabled()) or \
            isinstance(tracker, KiwiTCMS):
        tracker.add_testexecution_to_issue([link.execution], link.url)

    return response


@permissions_required('linkreference.delete_linkreference')
@rpc_method(name='TestExecution.remove_link')
def remove_link(query):
    """
    .. function:: RPC TestExecution.remove_link(query)

        Remove URL link from TestExecution

        :param query: Field lookups for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type query: dict
    """
    LinkReference.objects.filter(**query).delete()


@permissions_required('linkreference.view_linkreference')
@rpc_method(name='TestExecution.get_links')
def get_links(query):
    """
    .. function:: RPC TestExecution.get_links(query)

        Get URL links for the specified TestExecution

        :param query: Field lookups for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type query: dict
        :return: Serialized list of :class:`tcms.core.contrib.linkreference.models.LinkReference`
                 objects
        :rtype: dict
    """
    links = LinkReference.objects.filter(**query)
    serialier = Serializer(links)
    return serialier.serialize_queryset()
