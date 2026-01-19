# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.forms.models import model_to_dict
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.bugs.forms import NewBugFromRPCForm, SeverityForm
from tcms.bugs.models import Bug, Severity
from tcms.core.helpers import comments
from tcms.management.models import Tag
from tcms.rpc import utils
from tcms.rpc.decorators import permissions_required
from tcms.testruns.models import TestExecution


@permissions_required("bugs.add_bug_tags")
@rpc_method(name="Bug.add_tag")
def add_tag(bug_id, tag, **kwargs):
    """
    .. function:: RPC Bug.add_tag(bug_id, tag)

        Add one tag to the specified Bug.

        :param bug_id: PK of Bug to modify
        :type bug_id: int
        :param tag: Tag name to add
        :type tag: str
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :raises PermissionDenied: if missing *bugs.add_bug_tags* permission
        :raises Bug.DoesNotExist: if object specified by PK doesn't exist
        :raises Tag.DoesNotExist: if missing *management.add_tag* permission and *tag*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag, _ = Tag.get_or_create(request.user, tag)
    Bug.objects.get(pk=bug_id).tags.add(tag)


@permissions_required("bugs.delete_bug_tags")
@rpc_method(name="Bug.remove_tag")
def remove_tag(bug_id, tag):
    """
    .. function:: RPC Bug.remove_tag(bug_id, tag)

        Remove tag from a Bug.

        :param bug_id: PK of Bug to modify
        :type bug_id: int
        :param tag: Tag name to remove
        :type tag: str
        :raises PermissionDenied: if missing *bugs.delete_bug_tags* permission
        :raises DoesNotExist: if objects specified don't exist
    """
    Bug.objects.get(pk=bug_id).tags.remove(Tag.objects.get(name=tag))


@permissions_required("bugs.delete_bug")
@rpc_method(name="Bug.remove")
def remove(query):
    """
    .. function:: RPC Bug.remove(bug_id)

        Remove Bug object(s).

        :param query: Field lookups for :class:`tcms.bugs.models.Bug`
        :type query: dict
        :raises PermissionDenied: if missing *bugs.delete_bugtag* permission
    """
    Bug.objects.filter(**query).delete()


@permissions_required("bugs.view_bug")
@rpc_method(name="Bug.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Bug.filter(query)

        Get list of bugs.

        :param query: Field lookups for :class:`tcms.bugs.models.Bug`
        :type query: dict
        :return: List of serialized :class:`tcms.bugs.models.Bug` objects.
        :rtype: list
    """
    result = (
        Bug.objects.filter(**query)
        .values(
            "pk",
            "summary",
            "created_at",
            "product__name",
            "version__value",
            "build__name",
            "reporter__username",
            "assignee__username",
            "severity__name",
            "severity__color",
            "severity__icon",
        )
        .distinct()
    )
    return list(result)


@permissions_required("bugs.view_bug")
@rpc_method(name="Bug.filter_canonical")
def filter_canonical(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Bug.filter_canonical(query)

        Get a list of bugs where FKs are reported as IDs.

        :param query: Field lookups for :class:`tcms.bugs.models.Bug`
        :type query: dict
        :return: List of serialized :class:`tcms.bugs.models.Bug` objects.
        :rtype: list

    .. versionadded:: 15.3
    """
    result = (
        Bug.objects.filter(**query)
        .values(
            "id",
            "summary",
            "created_at",
            "status",
            "reporter",
            "assignee",
            "product",
            "version",
            "build",
            "severity",
        )
        .distinct()
    )
    return list(result)


@permissions_required("bugs.add_bug")
@rpc_method(name="Bug.create")
def create(values, **kwargs):
    """
    .. function:: RPC Bug.create(values)

        Create a new Bug object and store it in the database.

        :param values: Field values for :class:`tcms.bugs.models.Bug`
        :type values: dict
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`tcms.bugs.models.Bug` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *bugs.add_bug* permission

    .. versionadded:: 15.3
    """
    # mimic behavior specified in models.py b/c empty_value for BooleanField is False
    if "status" not in values:
        values["status"] = True

    if not values.get("reporter"):
        values["reporter"] = kwargs.get(REQUEST_KEY).user.pk

    form = NewBugFromRPCForm(values)
    if form.is_valid():
        bug = form.save()

        # auto_now_add will *always* set current date! see:
        # https://docs.djangoproject.com/en/6.0/ref/models/fields/#django.db.models.DateField.auto_now_add
        if "created_at" in form.cleaned_data:
            bug.created_at = form.cleaned_data["created_at"]
            bug.save()

        result = model_to_dict(bug)
        if "created_at" not in result:
            result["created_at"] = bug.created_at

        return result

    raise ValueError(list(form.errors.items()))


@permissions_required("bugs.view_severity")
@rpc_method(name="Severity.filter")
def severity_filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Severity.filter(query)

        Get list of bug severities.

        :param query: Field lookups for :class:`tcms.bugs.models.Severity`
        :type query: dict
        :return: List of serialized :class:`tcms.bugs.models.Severity` objects.
        :rtype: list

    .. versionadded:: 15.2
    """
    result = (
        Severity.objects.filter(**query)
        .values(
            "id",
            "name",
            "weight",
            "icon",
            "color",
        )
        .distinct()
    )
    return list(result)


@permissions_required("bugs.add_severity")
@rpc_method(name="Severity.create")
def severity_create(values):
    """
    .. function:: RPC Severity.create(values)

        Create a new Severity object and store it in the database.

        :param values: Field values for :class:`tcms.bugs.models.Severity`
        :type values: dict
        :return: Serialized :class:`tcms.bugs.models.Severity` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *bugs.add_severity* permission

    .. versionadded:: 15.2
    """
    form = SeverityForm(values)

    if form.is_valid():
        severity = form.save()
        return model_to_dict(severity)

    raise ValueError(list(form.errors.items()))


@permissions_required("django_comments.view_comment")
@rpc_method(name="Bug.get_comments")
def get_comments(bug_id):
    """
    .. function:: RPC Bug.get_comments(bug_id)

        Get all comments for selected Bug.

        :param bug_id: PK of a Bug object
        :type bug_id: int
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: list(dict)
        :raises PermissionDenied: if missing *django_comments.view_comment* permission

    .. versionadded:: 15.3
    """
    bug = Bug.objects.get(pk=bug_id)
    result = comments.get_comments(bug).values()
    return list(result)


@permissions_required("django_comments.add_comment")
@rpc_method(name="Bug.add_comment")
def add_comment(bug_id, comment, user_id=None, submit_date=None, **kwargs):
    """
    .. function:: RPC Bug.add_comment(bug_id, comment)

        Add comment to selected Bug.

        :param bug_id: PK of a Bug object
        :type bug_id: int
        :param comment: The text to add as a comment
        :type comment: str
        :param user_id: Override comment ``user`` field. Only super-user can use this!
        :type user_id: int
        :param submit_date: Override comment ``submit_date`` field. Only super-user can use this!
        :type submit_date: datetime.datetime
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: dict
        :raises PermissionDenied: if missing *django_comments.add_comment* permission

    .. versionadded:: 15.3
    """
    request_user = kwargs.get(REQUEST_KEY).user

    comment_author = request_user
    if user_id and request_user.is_superuser:
        comment_author = get_user_model().objects.get(pk=user_id)

    # only super-user can override this
    if not request_user.is_superuser:
        submit_date = None

    bug = Bug.objects.get(pk=bug_id)
    created = comments.add_comment([bug], comment, comment_author, submit_date)
    # we always create only one comment
    return model_to_dict(created[0])


@permissions_required("attachments.add_attachment")
@rpc_method(name="Bug.add_attachment")
def add_attachment(bug_id, filename, b64content, **kwargs):
    """
    .. function:: RPC Bug.add_attachment(bug_id, filename, b64content)

        Add attachment to the given Bug.

        :param bug_id: PK of Bug
        :type bug_id: int
        :param filename: File name of attachment, e.g. 'logs.txt'
        :type filename: str
        :param b64content: Base64 encoded content
        :type b64content: str
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
    """
    utils.add_attachment(
        bug_id,
        "bugs.Bug",
        kwargs.get(REQUEST_KEY).user,
        filename,
        b64content,
    )


@permissions_required("attachments.view_attachment")
@rpc_method(name="Bug.list_attachments")
def list_attachments(bug_id, **kwargs):
    """
    .. function:: RPC Bug.list_attachments(bug_id)

        List attachments for the given Bug.

        :param bug_id: PK of Bug to inspect
        :type bug_id: int
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: A list containing information and download URLs for attachements
        :rtype: list
        :raises Bug.DoesNotExist: if object specified by PK is missing

    .. versionadded:: 15.3
    """
    bug = Bug.objects.get(pk=bug_id)
    request = kwargs.get(REQUEST_KEY)
    return utils.get_attachments_for(request, bug)


@permissions_required("bugs.add_bug_executions")
@rpc_method(name="Bug.add_execution")
def add_execution(bug_id, execution_id):
    """
    .. function:: RPC Bug.add_execution(bug_id, execution_id)

        Add TestExecution to the specified Bug.

        :param bug_id: PK of Bug to modify
        :type bug_id: int
        :param execution_id: PK of TestExecution to be added
        :type execution_id: int
        :raises PermissionDenied: if missing *bugs.add_bug_executions* permission
        :raises Bug.DoesNotExist: if object specified by PK doesn't exist
        :raises TestExecution.DoesNotExist: if object specified by PK doesn't exist

    .. versionadded:: 15.3
    """
    bug = Bug.objects.get(pk=bug_id)
    execution = TestExecution.objects.get(pk=execution_id)
    bug.executions.add(execution)
