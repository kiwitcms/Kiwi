# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from django.utils import timezone
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.bugs.forms import NewBugFromRPCForm, SeverityForm
from tcms.bugs.models import Bug, Severity
from tcms.core.helpers import comments
from tcms.management.models import Tag
from tcms.rpc.decorators import permissions_required


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

    # although this field is required=False when not present Django
    # cannot deal with a NULL value so we set it to the current timestamp
    if "created_at" not in values:
        values["created_at"] = timezone.now().isoformat()

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
