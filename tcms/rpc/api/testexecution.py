# -*- coding: utf-8 -*-

from django.conf import settings
from django.forms.models import model_to_dict
from django.utils import timezone
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers import comments
from tcms.core.utils import form_errors_to_list
from tcms.rpc.api.forms.testrun import UpdateExecutionForm
from tcms.rpc.api.utils import tracker_from_url
from tcms.rpc.decorators import permissions_required
from tcms.testruns.models import TestExecution

# conditional import b/c this App can be disabled
if "tcms.bugs.apps.AppConfig" in settings.INSTALLED_APPS:
    from tcms.issuetracker.kiwitcms import KiwiTCMS
else:

    class KiwiTCMS:  # pylint: disable=remove-empty-class,nested-class-found,too-few-public-methods
        pass


__all__ = (
    "update",
    "filter",
    "history",
    "add_comment",
    "remove_comment",
    "add_link",
    "get_links",
    "remove_link",
)


@permissions_required("django_comments.add_comment")
@rpc_method(name="TestExecution.add_comment")
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


@permissions_required("django_comments.delete_comment")
@rpc_method(name="TestExecution.remove_comment")
def remove_comment(execution_id, comment_id=None):
    """
    .. function:: RPC TestExecution.remove_comment(execution_id, comment_id)

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


@permissions_required("django_comments.view_comment")
@rpc_method(name="TestExecution.get_comments")
def get_comments(execution_id):
    """
    .. function:: RPC TestExecution.get_comments(execution_id)

        Get all comments for selected test execution.

        :param execution_id: PK of a TestExecution object
        :type execution_id: int
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: dict
        :raises PermissionDenied: if missing *django_comments.view_comment* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)
    execution_comments = comments.get_comments(execution).values()
    return list(execution_comments)


@permissions_required("testruns.view_testexecution")
@rpc_method(name="TestExecution.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC TestExecution.filter(query)

        Perform a search and return the resulting list of test case executions.

        :param query: Field lookups for :class:`tcms.testruns.models.TestExecution`
        :type query: dict
        :return: List of serialized :class:`tcms.testruns.models.TestExecution` objects
        :rtype: list(dict)
    """
    return list(
        TestExecution.objects.filter(**query)
        .values(
            "id",
            "assignee",
            "assignee__username",
            "tested_by",
            "tested_by__username",
            "case_text_version",
            "start_date",
            "stop_date",
            "sortkey",
            "run",
            "case",
            "case__summary",
            "build",
            "build__name",
            "status",
            "status__name",
        )
        .distinct()
    )


@permissions_required("testruns.view_testexecution")
@rpc_method(name="TestExecution.history")
def history(execution_id):
    """
    .. function:: RPC TestExecution.history(execution_id)

        Return the history for the selected test execution.

        :param execution_id: PK of a TestExecution object
        :type execution_id: int
        :return: List of serialized :class:`tcms.core.history.KiwiHistoricalRecords` objects
        :rtype: list(dict)
        :raises PermissionDenied: if missing *testruns.view_testexecution* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)
    execution_history = (
        execution.history.all()
        .order_by("-history_date")
        .values(
            "history_user__username",
            "history_change_reason",
            "history_date",
            "history_change_reason",
        )
    )
    return list(execution_history)


@permissions_required("testruns.change_testexecution")
@rpc_method(name="TestExecution.update")
def update(execution_id, values, **kwargs):
    """
    .. function:: RPC TestExecution.update(execution_id, values)

        Update the selected TestExecution

        :param execution_id: PK of TestExecution to modify
        :type execution_id: int
        :param values: Field values for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :rtype: dict
        :raises ValueError: if data validations fail
        :raises PermissionDenied: if missing *testruns.change_testexecution* permission
    """
    test_execution = TestExecution.objects.get(pk=execution_id)

    if values.get("case_text_version") == "latest":
        values["case_text_version"] = test_execution.case.history.latest().history_id

    if values.get("status") and not values.get("tested_by"):
        values["tested_by"] = kwargs.get(REQUEST_KEY).user.id

    if values.get("status") and not values.get("build"):
        values["build"] = test_execution.run.build.pk

    form = UpdateExecutionForm(values, instance=test_execution)

    if form.is_valid():
        test_execution = form.save()
    else:
        raise ValueError(form_errors_to_list(form))

    # if this call updated TE.status then adjust timestamps
    if values.get("status"):
        now = timezone.now()
        if test_execution.status.weight != 0:
            test_execution.stop_date = now
        else:
            test_execution.stop_date = None
        test_execution.save()

        all_executions = TestExecution.objects.filter(run=test_execution.run)
        if (
            test_execution.status.weight != 0
            and not all_executions.filter(status__weight=0).exists()
        ):
            test_execution.run.stop_date = now
            test_execution.run.save()
        elif test_execution.status.weight == 0 and test_execution.run.stop_date:
            test_execution.run.stop_date = None
            test_execution.run.save()

    result = model_to_dict(test_execution)

    # augment result with additional information
    result["assignee__username"] = (
        test_execution.assignee.username if test_execution.assignee else None
    )
    result["tested_by__username"] = (
        test_execution.tested_by.username if test_execution.tested_by else None
    )
    result["case__summary"] = test_execution.case.summary
    result["build__name"] = test_execution.build.name
    result["status__name"] = test_execution.status.name

    return result


@permissions_required("linkreference.add_linkreference")
@rpc_method(name="TestExecution.add_link")
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

    if (
        link.is_defect
        and tracker is not None
        and update_tracker
        and not tracker.is_adding_testcase_to_issue_disabled()
    ) or isinstance(tracker, KiwiTCMS):
        tracker.add_testexecution_to_issue([link.execution], link.url)

    return response


@permissions_required("linkreference.delete_linkreference")
@rpc_method(name="TestExecution.remove_link")
def remove_link(query):
    """
    .. function:: RPC TestExecution.remove_link(query)

        Remove URL link from TestExecution

        :param query: Field lookups for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type query: dict
    """
    LinkReference.objects.filter(**query).delete()


@permissions_required("linkreference.view_linkreference")
@rpc_method(name="TestExecution.get_links")
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
    return list(
        LinkReference.objects.filter(**query).values(
            "id",
            "name",
            "url",
            "execution",
            "created_on",
            "is_defect",
        )
    )
