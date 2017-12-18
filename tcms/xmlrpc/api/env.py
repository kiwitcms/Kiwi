# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TCMSEnvGroup
from tcms.management.models import TCMSEnvProperty
from tcms.management.models import TCMSEnvValue
from tcms.xmlrpc.utils import parse_bool_value

__all__ = (
    'filter_groups',
    'filter_properties',
    'filter_values',
)


@rpc_method(name='Env.filter_groups')
def filter_groups(query):
    """
    .. function:: XML-RPC Env.filter_groups(query)

        Perform a search and return the resulting list of env groups.
        Parameter ``query`` is dict which recognizes the following
        keys:

        :param id: ID of env group
        :type id: int
        :param name: Name of env group
        :type name: str
        :param manager: Manager of this group. ForeignKey!
        :type manager: int or ``settings.AUTH_USER_MODEL`` object
        :param modified_by: Who modified the group. ForeignKey!
        :type modified_by: int or ``settings.AUTH_USER_MODEL`` object
        :param is_active: if this group is active or not
        :type is_active: bool
        :param property: Group property. ForeignKey
        :type property: int or :class:`tcms.management.models.TCMSEnvProperty`
        :returns: List of serialized env groups that match the query
        :rtype: list(dict)

    Query keys support the double-underscore field lookups from Django.
    For example to get all of env group with name containing 'Desktop'::

        >>> Env.filter_groups({'name__icontains': 'Desktop'})
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvGroup.to_xmlrpc(query)


@rpc_method(name='Env.filter_properties')
def filter_properties(query):
    """
    .. function:: XML-RPC Env.filter_properties(query)

        Performs a search and returns the resulting list of env properties.
        Parameter ``query`` is dict which recognizes the following
        keys:

        :param id: ID of env properties
        :type id: int
        :param name: Name of peroperty
        :type name: str
        :param is_active:
        :type is_active: bool
        :param group: ForeignKey: TCMSEnvGroup
        :type group: int or :class:`tcms.management.models.TCMSEnvGroup`
        :param value: ForeignKey: TCMSEnvValues
        :type value: int or :class:`tcms.management.models.TCMSEnvValues`
        :returns: List of serialized env properties matching the query
        :rtype: list(dict)

        For example to get all env properties containing 'Desktop'::

            >>> Env.filter_properties({'name__icontains': 'Desktop'})
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvProperty.to_xmlrpc(query)


@rpc_method(name='Env.filter_values')
def filter_values(query):
    """
    .. function:: XML-RPC Env.filter_values(query)

        Performs a search and returns the resulting list of env values.
        Parameter ``query`` is dict which recognizes the following
        keys:

        :param id: ID of env value
        :type id: int
        :param value: Object value
        :type value: str
        :param is_active:
        :type is_active: bool
        :param property: ForeignKey: TCMSEnvProperty
        :type property: int or :class:`tcms.management.models.TCMSEnvProperty`
        :returns: List of serialized env values matching the query
        :rtype: list(dict)

        For example to get all env values containing 'Desktop'::

            >>> Env.filter_values({'value__icontains': 'Desktop'})
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvValue.to_xmlrpc(query)
