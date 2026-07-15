from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import F
from django.db.models.functions import Coalesce
from django.forms.models import model_to_dict

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.helpers import comments
from tcms.management.models import Tag
from tcms.rpc import utils
from tcms.rpc.api.forms.testexecution import LinkReferenceForm
from tcms.rpc.api.forms.testrun import NewExecutionForm, UpdateExecutionForm
from tcms.rpc.api.utils import tracker_from_url
from tcms.rpc.decorators import permissions_required
from tcms.rpc.views import rpc_method
from tcms.testruns.models import TestExecution, TestExecutionProperty, TestExecutionTag

# conditional import b/c this App can be disabled
if "tcms.bugs.apps.AppConfig" in settings.INSTALLED_APPS:
    from tcms.issuetracker.kiwitcms import KiwiTCMS
else:

    class KiwiTCMS:  # pylint: disable=remove-empty-class,nested-class-found,too-few-public-methods
        pass


@rpc_method(
    name="TestExecution.add_comment",
    auth=permissions_required("django_comments.add_comment"),
    context_target="rpc_context",
)
def add_comment(
    execution_id, comment, user_id=None, submit_date=None, rpc_context=None
):
    """
    .. function:: RPC TestExecution.add_comment(execution_id, comment)

        Add comment to selected test execution.

        :param execution_id: PK of a TestExecution object
        :type execution_id: int
        :param comment: The text to add as a comment
        :type comment: str
        :param user_id: Override comment ``user`` field. Only super-user can use this!
        :type user_id: int
        :param submit_date: Override comment ``submit_date`` field. Only super-user can use this!
        :type submit_date: datetime.datetime
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: dict
        :raises PermissionDenied: if missing *django_comments.add_comment* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)

    request_user = rpc_context.request.user

    comment_author = request_user
    if user_id and request_user.is_superuser:
        comment_author = get_user_model().objects.get(pk=user_id)

    # only super-user can override this
    if not request_user.is_superuser:
        submit_date = None

    created = comments.add_comment([execution], comment, comment_author, submit_date)
    # we always create only one comment
    return model_to_dict(created[0])


@rpc_method(
    name="TestExecution.remove_comment",
    auth=permissions_required("django_comments.delete_comment"),
)
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


@rpc_method(
    name="TestExecution.get_comments",
    auth=permissions_required("django_comments.view_comment"),
)
def get_comments(execution_id):
    """
    .. function:: RPC TestExecution.get_comments(execution_id)

        Get all comments for selected test execution.

        :param execution_id: PK of a TestExecution object
        :type execution_id: int
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: list(dict)
        :raises PermissionDenied: if missing *django_comments.view_comment* permission
    """
    execution = TestExecution.objects.get(pk=execution_id)
    execution_comments = comments.get_comments(execution).values()
    return list(execution_comments)


@rpc_method(
    name="TestExecution.filter",
    auth=permissions_required("testruns.view_testexecution"),
)
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
        TestExecution.objects.annotate(
            expected_duration=(
                Coalesce("case__setup_duration", timedelta(0))
                + Coalesce("case__testing_duration", timedelta(0))
            ),
            actual_duration=F("stop_date") - F("start_date"),
        )
        .filter(**query)
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
            "status__icon",
            "status__color",
            "expected_duration",
            "actual_duration",
        )
        .order_by("id")
        .distinct()
    )


@rpc_method(
    name="TestExecution.history",
    auth=permissions_required("testruns.view_historicaltestexecution"),
)
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
        )
    )
    return list(execution_history)


@rpc_method(
    name="TestExecution.update",
    auth=permissions_required("testruns.change_testexecution"),
    context_target="rpc_context",
)
def update(execution_id, values, rpc_context=None):
    """
    .. function:: RPC TestExecution.update(execution_id, values)

        Update the selected TestExecution

        :param execution_id: PK of TestExecution to modify
        :type execution_id: int
        :param values: Field values for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :rtype: dict
        :raises ValueError: if data validations fail
        :raises PermissionDenied: if missing *testruns.change_testexecution* permission
    """
    request = rpc_context.request
    test_execution = TestExecution.objects.get(pk=execution_id)

    if values.get("case_text_version") == "latest":
        values["case_text_version"] = test_execution.case.history.latest().history_id

    if values.get("status") and not values.get("tested_by"):
        values["tested_by"] = request.user.id

    if values.get("status") and not values.get("build"):
        values["build"] = test_execution.run.build.pk

    form = UpdateExecutionForm(values, instance=test_execution, request=request)

    if form.is_valid():
        test_execution = form.save()
    else:
        raise ValueError(list(form.errors.items()))

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


@rpc_method(
    name="TestExecution.add_link",
    auth=permissions_required("linkreference.add_linkreference"),
    context_target="rpc_context",
)
def add_link(values, update_tracker=False, rpc_context=None):
    """
    .. function:: RPC TestExecution.add_link(values)

        Add new URL link to a TestExecution

        :param values: Field values for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type values: dict
        :param update_tracker: Automatically update Issue Tracker by placing a comment
                               linking back to the failed TestExecution.
        :type update_tracker: bool, default=False
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized
                 :class:`tcms.core.contrib.linkreference.models.LinkReference` object
        :rtype: dict
        :raises RuntimeError: if operation not successfull
        :raises ValueError: if input validation fails

        .. note::

            Always 'link' with IT instance if URL is from Kiwi TCMS own bug tracker!
    """
    # for backwards compatibility
    if "execution_id" in values:
        values["execution"] = values["execution_id"]
        del values["execution_id"]

    form = LinkReferenceForm(values)

    if form.is_valid():
        link = form.save()
    else:
        raise ValueError(list(form.errors.items()))

    request = rpc_context.request
    tracker = tracker_from_url(link.url, request)

    if (
        link.is_defect
        and tracker is not None
        and update_tracker
        and not tracker.is_adding_testcase_to_issue_disabled()
    ) or isinstance(tracker, KiwiTCMS):
        tracker.add_testexecution_to_issue([link.execution], link.url)

    return model_to_dict(link)


@rpc_method(
    name="TestExecution.remove_link",
    auth=permissions_required("linkreference.delete_linkreference"),
)
def remove_link(query):
    """
    .. function:: RPC TestExecution.remove_link(query)

        Remove URL link from TestExecution

        :param query: Field lookups for
                      :class:`tcms.core.contrib.linkreference.models.LinkReference`
        :type query: dict
    """
    LinkReference.objects.filter(**query).delete()


@rpc_method(
    name="TestExecution.get_links",
    auth=permissions_required("linkreference.view_linkreference"),
)
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


@rpc_method(
    name="TestExecution.properties",
    auth=permissions_required("testruns.view_testexecutionproperty"),
)
def properties(query):
    """
    .. function:: RPC TestExecution.properties(query)

        Return properties for a TestExecution

        :param query: Field lookups for
                      :class:`tcms.testruns.models.TestExecutionProperty`
        :type query: dict
        :return: Serialized list of :class:`tcms.testruns.models.TestExecutionProperty`
                 objects
        :rtype: dict
    """
    return list(
        TestExecutionProperty.objects.filter(**query).values(
            "id",
            "name",
            "value",
            "execution",
        )
    )


@rpc_method(
    name="TestExecution.add_property",
    auth=permissions_required("testruns.add_testexecutionproperty"),
)
def add_property(execution_id, name, value):
    """
    .. function:: TestExecution.add_property(execution_id, name, value)

        Add property to TestExecution! Duplicates are skipped without errors.

        :param execution_id: Primary key for :class:`tcms.testruns.models.TestExecution`
        :type execution_id: int
        :param name: Name of the property
        :type name: str
        :param value: Value of the property
        :type value: str
        :return: Serialized :class:`tcms.testruns.models.TestExecutionProperty` object.
        :rtype: dict
        :raises PermissionDenied: if missing *testruns.add_testexecutionproperty* permission

    .. versionadded:: 15.3
    """
    prop, _ = TestExecutionProperty.objects.get_or_create(
        execution_id=execution_id, name=name, value=value
    )
    return model_to_dict(prop)


@rpc_method(
    name="TestExecution.remove",
    auth=permissions_required("testruns.delete_testexecution"),
)
def remove(query):
    """
    .. function:: RPC TestExecution.remove(query)

        Remove a TestExecution.

        :param query: Field lookups for :class:`tcms.testruns.models.TestExecution`
        :type query: dict
        :raises PermissionDenied: if missing *testruns.delete_testexecution* permission
    """
    TestExecution.objects.filter(**query).delete()


@rpc_method(
    name="TestExecution.list_attachments",
    auth=permissions_required("attachments.view_attachment"),
    context_target="rpc_context",
)
def list_attachments(execution_id, rpc_context=None):
    """
    .. function:: RPC TestExecution.list_attachments(execution_id)

        List attachments for the given TestExecution.

        :param execution_id: PK of TestExecution to inspect
        :type execution_id: int
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: A list containing information and download URLs for attachements
        :rtype: list
        :raises TestExecution.DoesNotExit: if object specified by PK is missing

    .. versionadded:: 15.3
    """
    execution = TestExecution.objects.get(pk=execution_id)
    request = rpc_context.request
    return utils.get_attachments_for(request, execution)


@rpc_method(
    name="TestExecution.add_attachment",
    auth=permissions_required("attachments.add_attachment"),
    context_target="rpc_context",
)
def add_attachment(execution_id, filename, b64content, rpc_context=None):
    """
    .. function:: RPC TestExecution.add_attachment(execution_id, filename, b64content)

        Add attachment to the given TestExecution.

        :param execution_id: PK of TestExecution
        :type execution_id: int
        :param filename: File name of attachment, e.g. 'logs.txt'
        :type filename: str
        :param b64content: Base64 encoded content
        :type b64content: str
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext

    .. versionadded:: 15.3
    """
    utils.add_attachment(
        execution_id,
        "testruns.TestExecution",
        rpc_context.request.user,
        filename,
        b64content,
    )


@rpc_method(
    name="TestExecution.create",
    auth=permissions_required("testruns.add_testexecution"),
    context_target="rpc_context",
)
def create(values, rpc_context=None):
    """
    .. function:: RPC TestExecution.create(values)

        Create new TestExecution object and store it in the database.

        :param values: Field values for :class:`tcms.testruns.models.TestExecution`
        :type values: dict
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized :class:`tcms.testruns.models.TestExecution` object
        :rtype: dict
        :raises PermissionDenied: if missing *testruns.add_testexecution* permission
        :raises ValueError: if data validations fail

    .. versionadded:: 15.3
    """
    request = rpc_context.request
    form = NewExecutionForm(values, request=request)

    if form.is_valid():
        test_execution = form.save()
        return model_to_dict(test_execution)

    raise ValueError(list(form.errors.items()))


@rpc_method(
    name="TestExecution.add_tag",
    auth=permissions_required("testruns.add_testexecutiontag"),
    context_target="rpc_context",
)
def add_tag(execution_id, tag_name, rpc_context=None):
    """
    .. function:: RPC TestExecution.add_tag(execution_id, tag_name)

        Add one tag to the specified test execution.

        :param execution_id: PK of TestExecution to modify
        :type execution_id: int
        :param tag_name: Tag name to add
        :type tag_name: str
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized list of :class:`tcms.management.models.Tag` objects
        :rtype: dict
        :raises PermissionDenied: if missing *testruns.add_testexecutiontag* permission
        :raises TestExecution.DoesNotExist: if object specified by PK doesn't exist
        :raises Tag.DoesNotExist: if missing *management.add_tag* permission and *tag_name*
                 doesn't exist in the database!

    .. versionadded:: 16.1
    """
    request = rpc_context.request
    tag, _ = Tag.get_or_create(request.user, tag_name)
    test_execution = TestExecution.objects.get(pk=execution_id)
    TestExecutionTag.objects.get_or_create(execution=test_execution, tag=tag)
    return list(test_execution.tag.values("id", "name"))


@rpc_method(
    name="TestExecution.remove_tag",
    auth=permissions_required("testruns.delete_testexecutiontag"),
)
def remove_tag(execution_id, tag_name):
    """
    .. function:: RPC TestExecution.remove_tag(execution_id, tag_name)

        Remove one tag from the specified test execution.

        :param execution_id: PK of TestExecution to modify
        :type execution_id: int
        :param tag_name: Tag name to remove
        :type tag_name: str
        :raises PermissionDenied: if missing *testruns.delete_testexecutiontag* permission
        :raises TestExecution.DoesNotExist: if object specified by PK doesn't exist

    .. versionadded:: 16.1
    """
    test_execution = TestExecution.objects.get(pk=execution_id)
    TestExecutionTag.objects.filter(
        execution=test_execution, tag__name=tag_name
    ).delete()
    return list(test_execution.tag.values("id", "name"))
