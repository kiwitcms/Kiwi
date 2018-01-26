# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TestBuild
from tcms.xmlrpc.decorators import permissions_required
from tcms.xmlrpc.utils import pre_check_product, parse_bool_value

__all__ = (
    'check_build', 'create', 'get', 'update'
)


@rpc_method(name='Build.check_build')
def check_build(name, product):
    """
    .. function:: XML-RPC Build.check_build(name, product)

        Looks up and returns a build by name.

        :param name: name of the build
        :type name: str
        :param product: Product ID or name to which this build belongs
        :type product: int or str
        :return: Serialized :class:`tcms.management.models.TestBuild` object
        :rtype: dict
        :raises: TestBuild.DoesNotExist if build not found
    """
    p = pre_check_product(values=product)
    return TestBuild.objects.get(name=name, product=p).serialize()


@rpc_method(name='Build.create')
@permissions_required('management.add_testbuild')
def create(values):
    """
    .. function:: XML-RPC Build.create(values)

        Creates a new build object and stores it in the database.
        ``values`` is a dict matching the fields of the
        :class:`tcms.management.models.TestBuild` model:

        :param product: **required** ID or name of Product to which this Build belongs
        :type product: int or str
        :param name: **required** name of the build (aka build version string)
        :type name: str
        :param description: optional description
        :type str:
        :param is_active: Optional, default to True
        :type is_active: bool
        :return: Serialized :class:`tcms.management.models.TestBuild` object
        :rtype: dict
        :raises: ValueError if product or name not specified
        :raises: PermissionDenied if missing *management.add_testbuild* permission
    """
    if not values.get('product') or not values.get('name'):
        raise ValueError('Product and name are both required.')

    p = pre_check_product(values)

    return TestBuild.objects.create(
        product=p,
        name=values['name'],
        description=values.get('description'),
        is_active=parse_bool_value(values.get('is_active', True))
    ).serialize()


@rpc_method(name='Build.get')
def get(build_id):
    """
    .. function:: XML-RPC Build.get(build_id)

        Get an existing build from the database.

        :param build_id: the object ID
        :type build_id: int
        :return: Serialized :class:`tcms.management.models.TestBuild` object
        :rtype: dict
        :raises: TestBuild.DoesNotExist if build not found
    """
    return TestBuild.objects.get(build_id=build_id).serialize()


@permissions_required('management.change_testbuild')
@rpc_method(name='Build.update')
def update(build_id, values):
    """
    .. function:: XML-RPC Build.update(build_id, values)

        Updates the fields of the selected ``build_id``.
        ``values`` is a dict matching the fields of the
        :class:`tcms.management.models.TestBuild` model:

        :param product: ID or name of Product to which this Build belongs
        :type product: int or str
        :param name: Name of the build (aka build version string)
        :type name: str
        :param description: Description
        :type str:
        :param is_active: If the Build is active
        :type is_active: bool
        :return: Serialized :class:`tcms.management.models.TestBuild` object
        :rtype: dict
        :raises: TestBuild.DoesNotExist if build not found
        :raises: PermissionDenied if missing *management.change_testbuild* permission
    """
    tb = TestBuild.objects.get(build_id=build_id)

    def _update_value(obj, name, value):
        setattr(obj, name, value)
        update_fields.append(name)

    update_fields = list()
    if values.get('product'):
        _update_value(tb, 'product', pre_check_product(values))
    if values.get('name'):
        _update_value(tb, 'name', values['name'])
    if values.get('description'):
        _update_value(tb, 'description', values['description'])
    if values.get('is_active') is not None:
        _update_value(tb, 'is_active', parse_bool_value(values.get(
            'is_active', True)))

    tb.save(update_fields=update_fields)

    return tb.serialize()
