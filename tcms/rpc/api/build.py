# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import Build
from tcms.rpc.decorators import permissions_required
from tcms.rpc.utils import parse_bool_value, pre_check_product

__all__ = (
    'create',
    'update',
    'filter',
)


@rpc_method(name='Build.filter')
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC Build.filter(query)

        Search and return builds matching query.

        :param query: Field lookups for :class:`tcms.management.models.Build`
        :type query: dict
        :return: List of serialized :class:`tcms.management.models.Build` objects
        :rtype: list(dict)
    """

    if query is None:
        query = {}
    return Build.to_xmlrpc(query)


@rpc_method(name='Build.create')
@permissions_required('management.add_build')
def create(values):
    """
    .. function:: XML-RPC Build.create(values)

        Create a new build object and store it in the database.

        :param values: Field values for :class:`tcms.management.models.Build`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Build` object
        :rtype: dict
        :raises: ValueError if product or name not specified
        :raises: PermissionDenied if missing *management.add_build* permission
    """
    if not values.get('product') or not values.get('name'):
        raise ValueError('Product and name are both required.')

    return Build.objects.create(
        product=pre_check_product(values),
        name=values['name'],
        is_active=parse_bool_value(values.get('is_active', True))
    ).serialize()


@permissions_required('management.change_build')
@rpc_method(name='Build.update')
def update(build_id, values):
    """
    .. function:: XML-RPC Build.update(build_id, values)

        Updates the fields of the selected build.

        :param build_id: PK of Build to modify
        :type build_id: int
        :param values: Field values for :class:`tcms.management.models.Build`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Build` object
        :rtype: dict
        :raises: Build.DoesNotExist if build not found
        :raises: PermissionDenied if missing *management.change_build* permission
    """
    selected_build = Build.objects.get(pk=build_id)

    def _update_value(obj, name, value):
        setattr(obj, name, value)
        update_fields.append(name)

    update_fields = list()
    if values.get('product'):
        _update_value(selected_build, 'product', pre_check_product(values))
    if values.get('name'):
        _update_value(selected_build, 'name', values['name'])
    if values.get('is_active') is not None:
        _update_value(selected_build, 'is_active', parse_bool_value(values.get(
            'is_active', True)))

    selected_build.save(update_fields=update_fields)

    return selected_build.serialize()
