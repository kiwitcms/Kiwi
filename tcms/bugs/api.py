# -*- coding: utf-8 -*-

from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.bugs.models import Bug
from tcms.management.models import Tag
from tcms.rpc.decorators import permissions_required

__all__ = (
    'add_tag',
    'remove_tag',
    'filter',
    'remove',
)


@permissions_required('bugs.add_bugtag')
@rpc_method(name='Bug.add_tag')
def add_tag(bug_id, tag, **kwargs):
    """
    .. function:: XML-RPC Bug.add_tag(bug_id, tag)

        Add one tag to the specified Bug.

        :param bug_id: PK of Bug to modify
        :type bug_id: int
        :param tag: Tag name to add
        :type tag: str
        :return: None
        :raises: PermissionDenied if missing *bugs.add_bugtag* permission
        :raises: Bug.DoesNotExist if object specified by PK doesn't exist
        :raises: Tag.DoesNotExist if missing *management.add_tag* permission and *tag*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag, _ = Tag.get_or_create(request.user, tag)
    Bug.objects.get(pk=bug_id).tags.add(tag)


@permissions_required('bugs.delete_bugtag')
@rpc_method(name='Bug.remove_tag')
def remove_tag(bug_id, tag):
    """
    .. function:: XML-RPC Bug.remove_tag(bug_id, tag)

        Remove tag from a Bug.

        :param bug_id: PK of Bug to modify
        :type bug_id: int
        :param tag: Tag name to remove
        :type tag: str
        :return: None
        :raises: PermissionDenied if missing *bugs.delete_bugtag* permission
        :raises: DoesNotExist if objects specified don't exist
    """
    Bug.objects.get(pk=bug_id).tags.remove(
        Tag.objects.get(name=tag)
    )


@permissions_required('bugs.delete_bug')
@rpc_method(name='Bug.remove')
def remove(query):
    """
    .. function:: XML-RPC Bug.remove(bug_id)

        Remove Bug object(s).

        :param query: Field lookups for :class:`tcms.bugs.models.Bug`
        :type query: dict
        :return: None
        :raises: PermissionDenied if missing *bugs.delete_bugtag* permission
    """
    Bug.objects.filter(**query).delete()


@rpc_method(name='Bug.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Bug.filter(query)

        Get list of bugs.

        :param query: Field lookups for :class:`tcms.bugs.models.Bug`
        :type query: dict
        :return: List of serialized :class:`tcms.bugs.models.Bug` objects.
    """
    result = Bug.objects.filter(**query).values(
        'pk',
        'summary',
        'created_at',
        'product__name',
        'version__value',
        'build__name',
        'reporter__username',
        'assignee__username',
    )
    return list(result)
