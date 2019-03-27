# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.xmlrpc.utils import parse_bool_value
from tcms.xmlrpc.decorators import permissions_required


User = get_user_model()  # pylint: disable=invalid-name


__all__ = (
    'update',
    'filter',
    'join_group',
)


def _get_user_dict(user):
    user_dict = XMLRPCSerializer(model=user).serialize_model()
    if 'password' in user_dict:
        del user_dict['password']
    return user_dict


@rpc_method(name='User.filter')
def filter(query=None, **kwargs):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC User.filter(query)

        Search and return the resulting list of users.

        :param query: Field lookups for :class:`django.contrib.auth.models.User`
        :type query: dict
        :return: Serialized :class:`django.contrib.auth.models.User` object without
                 the password field!
        :rtype: dict

    .. note::

        If query is ``None`` will return the user issuing the RPC request.
    """
    if not query:
        query = {'pk': kwargs.get(REQUEST_KEY).user.pk}

    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    users = User.objects.filter(**query)

    filtered_users = []
    for user in users:
        filtered_users.append(_get_user_dict(user))

    return filtered_users


@rpc_method(name='User.update')
def update(user_id, values, **kwargs):
    """
    .. function:: XML-RPC User.update(user_id, values)

        Updates the fields of the selected user. Can be used to update
        password as well!

        :param user_id: PK of user to update
        :type user_id: int
        :param values: Field values for :class:`django.contrib.auth.models.User`
        :type values: dict
        :return: Serialized :class:`django.contrib.auth.models.User` object
        :raises: PermissionDenied if missing the *auth.change_user* permission
                 when updating another user or when passwords don't match.

        .. note::

            If ``user_id`` is None will update the user issuing the RPC request.

        .. warning::

            Changing the password for another user via RPC is not allowed!
    """
    request = kwargs.get(REQUEST_KEY)
    if user_id:
        user_being_updated = User.objects.get(pk=user_id)
    else:
        user_being_updated = request.user

    editable_fields = ('first_name', 'last_name', 'email', 'password')
    can_change_user = request.user.has_perm('auth.change_user')

    is_updating_other = request.user != user_being_updated
    # If changing other's attributes, current user must have proper permission
    if is_updating_other and not can_change_user:
        raise PermissionDenied('Permission denied')

    update_fields = []
    for field in editable_fields:
        if not values.get(field):
            continue

        update_fields.append(field)
        if field == 'password':
            if is_updating_other:
                raise PermissionDenied('Password updates for other users are not allowed via RPC!')

            old_password = values.get('old_password')
            if not old_password:
                raise PermissionDenied('Old password is required')

            if not user_being_updated.check_password(old_password):
                raise PermissionDenied('Password is incorrect')

            user_being_updated.set_password(values['password'])
        else:
            setattr(user_being_updated, field, values[field])

    user_being_updated.save(update_fields=update_fields)
    return _get_user_dict(user_being_updated)


@permissions_required('auth.change_user')
@rpc_method(name='User.join_group')
def join_group(username, groupname):
    """
    .. function:: XML-RPC User.join_group(username, groupname)

        Add user to a group specified by name.

        :param username: Username to modify
        :type username: str
        :param groupname: Name of group to join, must exist!
        :type groupname: str
        :return: None
        :raises: PermissionDenied if missing *auth.change_user* permission
    """
    user = User.objects.get(username=username)
    group = Group.objects.get(name=groupname)
    user.groups.add(group)
