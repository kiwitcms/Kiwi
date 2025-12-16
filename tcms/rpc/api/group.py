# Copyright (c) 2025 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.contrib.auth.models import Group
from django.db.models import Value
from django.db.models.functions import Concat
from modernrpc.core import rpc_method

from tcms.rpc.decorators import permissions_required


@permissions_required("auth.view_group")
@rpc_method(name="Group.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Group.filter(query)

        Search and return the resulting list of groups.

        :param query: Field lookups for :class:`django.contrib.auth.models.Group`
        :type query: dict
        :return: Serialized list of :class:`django.contrib.auth.models.Group` objects
        :rtype: list(dict)
        :raises PermissionDenied: if missing the *auth.view_group* permission

    .. versionadded:: 15.3
    """
    return list(
        Group.objects.filter(**query)
        .values(
            "id",
            "name",
        )
        .distinct()
    )


@permissions_required("auth.view_group")
@rpc_method(name="Group.permissions")
def permissions(name):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Group.permissions(query)

        Search and return the resulting list of permissions for a particular group.

        :param name: Name of :class:`django.contrib.auth.models.Group`
        :type name: str
        :return: Serialized list of permission labels
        :rtype: list(str)
        :raises PermissionDenied: if missing the *auth.view_group* permission
        :raises DoesNotExist: if group doesn't exist

    .. versionadded:: 15.3
    """
    group = Group.objects.get(name=name)

    return list(
        group.permissions.annotate(
            perm_name=Concat("content_type__app_label", Value("."), "codename")
        )
        .values_list("perm_name", flat=True)
        .distinct()
    )
