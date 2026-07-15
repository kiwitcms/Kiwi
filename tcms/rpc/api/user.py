from attachments.models import Attachment
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.forms.models import model_to_dict

from tcms.rpc import utils
from tcms.rpc.decorators import permissions_required
from tcms.rpc.views import rpc_method
from tcms.utils import user as user_utils


def get_queryset(request):
    queryset = get_user_model().objects.all()
    if (
        request
        and hasattr(request, "tenant")
        and request.tenant.schema_name != "public"
    ):
        queryset = request.tenant.authorized_users.all()
    return queryset


def _get_user_dict(user):
    user_dict = model_to_dict(user)

    for field in (
        "password",
        "groups",
        "user_permissions",
        "date_joined",
        "last_login",
    ):
        if field in user_dict:
            del user_dict[field]

    return user_dict


@rpc_method(
    name="User.filter",
    auth=permissions_required("auth.view_user"),
    context_target="rpc_context",
)
def filter(query=None, rpc_context=None):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC User.filter(query)

        Search and return the resulting list of users.

        :param query: Field lookups for :class:`django.contrib.auth.models.User`
        :type query: dict
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized list of :class:`django.contrib.auth.models.User` objects
                 without the password field
        :rtype: list(dict)
        :raises PermissionDenied: if missing the *auth.view_user* permission

    .. note::

        If query is ``None`` will return the user issuing the RPC request.
    """
    request = rpc_context.request
    if not query:
        query = {"pk": request.user.pk}

    return list(
        get_queryset(request)
        .filter(**query)
        .values(
            "email",
            "first_name",
            "id",
            "is_active",
            "is_staff",
            "is_superuser",
            "last_name",
            "username",
        )
        .order_by("id")
        .distinct()
    )


@rpc_method(
    name="User.update",
    auth=None,
    context_target="rpc_context",
)
def update(
    user_id, values, rpc_context=None
):  # pylint: disable=missing-api-permissions-required
    """
    .. function:: RPC User.update(user_id, values)

        Updates the fields of the selected user. Can be used to update
        password as well!

        :param user_id: PK of user to update
        :type user_id: int
        :param values: Field values for :class:`django.contrib.auth.models.User`
        :type values: dict
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized :class:`django.contrib.auth.models.User` object
        :rtype: dict
        :raises PermissionDenied: if missing the *auth.change_user* permission
                 when updating another user or when passwords don't match.

        .. note::

            If ``user_id`` is None will update the user issuing the RPC request.

        .. warning::

            Changing the password for another user via RPC is not allowed!
    """
    request = rpc_context.request
    if user_id:
        user_being_updated = get_queryset(request).get(pk=user_id)
    else:
        user_being_updated = request.user

    editable_fields = ("first_name", "last_name", "email", "password")
    can_change_user = request.user.has_perm("auth.change_user")

    is_updating_other = request.user != user_being_updated
    # If changing other's attributes, current user must have proper permission
    if is_updating_other and not can_change_user:
        raise PermissionDenied("Permission denied")

    update_fields = []
    for field in editable_fields:
        if not values.get(field):
            continue

        update_fields.append(field)
        if field == "password":
            if is_updating_other:
                raise PermissionDenied(
                    "Password updates for other users are not allowed via RPC!"
                )

            old_password = values.get("old_password")
            if not old_password:
                raise PermissionDenied("Old password is required")

            if not user_being_updated.check_password(old_password):
                raise PermissionDenied("Password is incorrect")

            user_being_updated.set_password(values["password"])
        else:
            setattr(user_being_updated, field, values[field])

    user_being_updated.save(update_fields=update_fields)
    return _get_user_dict(user_being_updated)


@rpc_method(
    name="User.deactivate",
    auth=permissions_required("auth.change_user"),
    context_target="rpc_context",
)
def deactivate(query, rpc_context=None):
    """
    .. function:: RPC User.deactivate(query)

        Deactivate the selected user(s) so that they cannot login again!

        :param query: Field lookups for :class:`django.contrib.auth.models.User`
        :type query: dict
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Serialized list of :class:`django.contrib.auth.models.User` objects
        :rtype: list(dict)
        :raises PermissionDenied: if missing the *auth.change_user* permission
                 when updating another user or when passwords don't match.

        Specify by user ID::

            >>> User.deactivate({'pk': 123})

        Specify multiple users by ID::

            >>> User.deactivate({'pk__in': [123, 456]})

        Specify by username::

            >>> User.deactivate({'username': 'john-doe'})

        Specify by email::

            >>> User.deactivate({'email__icontains': '@example.com'})
            >>> User.deactivate({'email__startswith': 'mia@'})
    """
    request = rpc_context.request
    result = []
    for user in get_queryset(request).filter(**query):
        user_utils.deactivate(user)

        result.append(_get_user_dict(user))

    return result


@rpc_method(
    name="User.join_group",
    auth=permissions_required("auth.change_user"),
    context_target="rpc_context",
)
def join_group(username, groupname, rpc_context=None):
    """
    .. function:: RPC User.join_group(username, groupname)

        Add user to a group specified by name.

        :param username: Username to modify
        :type username: str
        :param groupname: Name of group to join, must exist!
        :type groupname: str
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :raises PermissionDenied: if missing *auth.change_user* permission
    """
    request = rpc_context.request
    user = get_queryset(request).get(username=username)
    group = Group.objects.get(name=groupname)
    user.groups.add(group)


@rpc_method(
    name="User.add_attachment",
    auth=permissions_required("attachments.add_attachment"),
    context_target="rpc_context",
)
def add_attachment(filename, b64content, rpc_context=None):
    """
    .. function:: RPC User.add_attachment(filename, b64content)

        Attach a file under the currently logged-in user!

        This method is meant to be used by SimpleMDE combined with post_save
        processing for various models like TestPlan and TestCase. While files
        uploaded by this method will be attached and available (if you know their URL),
        there is no UI to see all of the files uploaded by a certain user or
        manage them!

        :param filename: File name of attachment, e.g. 'logs.txt'
        :type filename: str
        :param b64content: Base64 encoded content
        :type b64content: str
        :param rpc_context: Provides access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :type rpc_context: modernrpc.core.RpcRequestContext
        :return: Information about the attachment
        :rtype: dict
    """
    user = rpc_context.request.user
    utils.add_attachment(
        user.pk,
        settings.AUTH_USER_MODEL,
        user,
        filename,
        b64content,
    )

    # take the last attachment for this user and return information about it
    attachment = (
        Attachment.objects.attachments_for_object(user).order_by("created").last()
    )
    return {
        "url": attachment.attachment_file.url,
        "filename": attachment.filename,
    }
