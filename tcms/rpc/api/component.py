# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.management.models import Component
from tcms.rpc.decorators import permissions_required
from tcms.rpc.utils import pre_check_product

User = get_user_model()  # pylint: disable=invalid-name


__all__ = (
    'create',
    'update',
    'filter',
)


@rpc_method(name='Component.filter')
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Component.filter(query)

        Search and return the resulting list of components.

        :param query: Field lookups for :class:`tcms.management.models.Component`
        :type query: dict
        :return: List of serialized :class:`tcms.management.models.Component` objects
        :rtype: list(dict)
    """
    return Component.to_xmlrpc(query)


@permissions_required('management.add_component')
@rpc_method(name='Component.create')
def create(values, **kwargs):
    """
    .. function:: XML-RPC Component.create(values)

        Create new component.

        :param values: Field values for :class:`tcms.management.models.Component`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises: PermissionDenied if missing *management.add_component* permission

    .. note::

        If ``initial_owner_id`` or ``initial_qa_owner_id`` are
        not specified or don't exist in the database these fields are set to the
        user issuing the RPC request!
    """
    initial_owner_id = values.get('initial_owner_id', None)
    initial_qa_contact_id = values.get('initial_qa_contact_id', None)
    product = pre_check_product(values)

    request = kwargs.get(REQUEST_KEY)
    if User.objects.filter(pk=initial_owner_id).exists():
        _initial_owner_id = initial_owner_id
    else:
        _initial_owner_id = request.user.pk

    if User.objects.filter(pk=initial_qa_contact_id).exists():
        _initial_qa_contact_id = initial_qa_contact_id
    else:
        _initial_qa_contact_id = request.user.pk

    return Component.objects.create(
        name=values['name'],
        product=product,
        initial_owner_id=_initial_owner_id,
        initial_qa_contact_id=_initial_qa_contact_id,
    ).serialize()


@permissions_required('management.change_component')
@rpc_method(name='Component.update')
def update(component_id, values):
    """
    .. function:: XML-RPC Component.update

        Update component with new values.

        :param component_id: PK of Component to be updated
        :type component_id: int
        :param values: Fields and values to be updated
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises: ValueError if ``name`` is missing or empty string
        :raises: PermissionDenied if missing *management.change_component* permission
    """
    if not isinstance(values, dict) or 'name' not in values:
        raise ValueError('Component name is not in values {0}.'.format(values))

    name = values['name']
    if not isinstance(name, str) or not name:
        raise ValueError('Component name {0} is not a string value.'.format(name))

    component = Component.objects.get(pk=int(component_id))
    component.name = name
    if values.get('initial_owner_id') and \
            User.objects.filter(pk=values['initial_owner_id']).exists():
        component.initial_owner_id = values['initial_owner_id']
    if values.get('initial_qa_contact_id') and \
            User.objects.filter(pk=values['initial_qa_contact_id']).exists():
        component.initial_qa_contact_id = values['initial_qa_contact_id']
    component.save()
    return component.serialize()
