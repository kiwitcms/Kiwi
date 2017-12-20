# -*- coding: utf-8 -*-

from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.xmlrpc.utils import parse_bool_value
from tcms.xmlrpc.decorators import permissions_required

__all__ = (
    'filter',
    'get',
    'update',
    'join'
)


def get_user_dict(user):
    u = XMLRPCSerializer(model=user)
    u = u.serialize_model()
    if 'password' in u:
        del u['password']
    return u


@rpc_method(name='User.filter')
def filter(query):
    """
    Description: Performs a search and returns the resulting list of test cases

    Params:      $query - Hash: keys must match valid search fields.

        +------------------------------------------------------------------+
        |                 Case Search Parameters                           |
        +------------------------------------------------------------------+
        |        Key          |          Valid Values                      |
        | id                  | Integer: ID                                |
        | username            | String: User name                          |
        | first_name          | String: User first name                    |
        | last_name           | String: User last  name                    |
        | email               | String Email                               |
        | is_active           | Boolean: Return the active users           |
        | groups              | ForeignKey: AuthGroup                      |
        +------------------------------------------------------------------+

    Returns:     Array: Matching test cases are retuned in a list of hashes.

    Example:
    >>> User.filter({'username__startswith': 'x'})
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    users = User.objects.filter(**query)
    return [get_user_dict(u) for u in users]


@rpc_method(name='User.get')
def get(id=None, **kwargs):
    """
    Description: Used to load an existing user from the database.

    Params:      $id - Integer/String: An integer representing the ID in the
                       database. If parameter is None then return information
                       about the currently logged in user.

    Returns:     A blessed User object Hash

    Example:
    >>> User.get(2206)
    """
    if id is None:
        user = kwargs.get(REQUEST_KEY).user
    else:
        user = User.objects.get(pk=id)
    return get_user_dict(user)


@rpc_method(name='User.update')
def update(values, id=None, **kwargs):
    """
    Description: Updates the fields of the selected user. it also can change
                 the informations of other people if you have permission.

    Params:      $values   - Hash of keys matching TestCase fields and the new
                             values to set each field to.

                 $id       - Integer/String(Optional)
                             Integer: A single TestCase ID.
                             String:  A comma string of User ID.
                             Default: The ID of myself

    Returns:     A blessed User object Hash

    +--------------+--------+-----------------------------------------+
    | Field        | Type   | Null                                    |
    +--------------+--------+-----------------------------------------+
    | first_name   | String | Optional                                |
    | last_name    | String | Optional(Required if changes category)  |
    | email        | String | Optional                                |
    | password     | String | Optional                                |
    | old_password | String | Required by password                    |
    +--------------+--------+-----------------------------------------+

    Example:
    >>> User.update({'first_name': 'foo'})
    >>> User.update({'password': 'foo', 'old_password': '123'})
    >>> User.update({'password': 'foo', 'old_password': '123'}, 2206)
    """
    request = kwargs.get(REQUEST_KEY)
    if id:
        user_being_updated = User.objects.get(pk=id)
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
    return get_user_dict(user_being_updated)


@permissions_required('auth.change_user')
@rpc_method(name='User.join')
def join(username, groupname):
    """
    Description: Add user to a group specified by name.

    Returns: None

    Raises: PermissionDenied
            Object.DoesNotExist

    Example:
    >>> User.join('username', 'groupname')
    """
    user = User.objects.get(username=username)
    group = Group.objects.get(name=groupname)

    user.groups.add(group)
