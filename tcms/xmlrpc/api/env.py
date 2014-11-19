# -*- coding: utf-8 -*-

from tcms.xmlrpc.decorators import log_call
from tcms.management.models import TCMSEnvGroup
from tcms.management.models import TCMSEnvProperty
from tcms.management.models import TCMSEnvValue
from tcms.xmlrpc.utils import parse_bool_value

__all__ = (
    'filter_groups',
    'filter_properties',
    'filter_values',
    'get_properties',
    'get_values',
)

__xmlrpc_namespace__ = 'TestEnv'


@log_call(namespace=__xmlrpc_namespace__)
def filter_groups(request, query):
    """
    Description: Performs a search and returns the resulting list of env groups.

    Params:      $query - Hash: keys must match valid search fields.

    +------------------------------------------------------------------+
    |               Product Search Parameters                          |
    +------------------------------------------------------------------+
    |        Key          |          Valid Values                      |
    | id                  | Integer: ID of env group                   |
    | name                | String                                     |
    | manager             | ForeignKey: Auth.user                      |
    | modified_by         | ForeignKey: Auth.user                      |
    | is_active           | Boolean                                    |
    | property            | ForeignKey: TCMSEnvProperty                |
    +------------------------------------------------------------------+

    Returns:     Array: Matching env groups are retuned in a list of hashes.

    Example:
    # Get all of env group name contains 'Desktop'
    >>> Env.filter_groups({'name__icontains': 'Desktop'})
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvGroup.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def filter_properties(request, query):
    """
    Description: Performs a search and returns the resulting list of env properties.

    Params:      $query - Hash: keys must match valid search fields.

    +------------------------------------------------------------------+
    |               Product Search Parameters                          |
    +------------------------------------------------------------------+
    |        Key          |          Valid Values                      |
    | id                  | Integer: ID of env properties              |
    | name                | String                                     |
    | is_active           | Boolean                                    |
    | group               | ForeignKey: TCMSEnvGroup                   |
    | value               | ForeignKey: TCMSEnvValues                   |
    +------------------------------------------------------------------+

    Returns:     Array: Matching env properties are retuned in a list of hashes.

    Example:
    # Get all of env properties name contains 'Desktop'
    >>> Env.filter_properties({'name__icontains': 'Desktop'})
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvProperty.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def filter_values(request, query):
    """
    Description: Performs a search and returns the resulting list of env properties.

    Params:      $query - Hash: keys must match valid search fields.

    +------------------------------------------------------------------+
    |               Product Search Parameters                          |
    +------------------------------------------------------------------+
    |        Key          |          Valid Values                      |
    | id                  | Integer: ID of env value                   |
    | value               | String                                     |
    | is_active           | Boolean                                    |
    | property            | ForeignKey: TCMSEnvProperty                |
    +------------------------------------------------------------------+

    Returns:     Array: Matching env values are retuned in a list of hashes.

    Example:
    # Get all of env values name contains 'Desktop'
    >>> Env.filter_values({'name__icontains': 'Desktop'})
    """
    if 'is_active' in query:
        query['is_active'] = parse_bool_value(query['is_active'])
    return TCMSEnvValue.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_properties(request, env_group_id=None, is_active=True):
    """
    Description: Get the list of properties associated with this env group.

    Params:      $env_group_id - Integer: env_group_id of the env group in the Database
                                 Return all of properties when the argument is not specific.
                 $is_active    - Boolean: True to only include builds where is_active is true.
                                 Default: True
    Returns:     Array: Returns an array of env properties objects.

    Example:
    # Get all of properties
    >>> Env.get_properties()
    # Get the properties in group 10
    >>> Env.get_properties(10)
    """
    query = {'is_active': parse_bool_value(is_active)}
    if env_group_id:
        query['group__pk'] = env_group_id

    return TCMSEnvProperty.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_values(request, env_property_id=None, is_active=True):
    """
    Description: Get the list of values associated with this env property.

    Params:      $env_property_id - Integer: env_property_id of the env property in the Database
                                    Return all of values when the argument is not specific.
                 $is_active       - Boolean: True to only include builds where is_active is true.
                                    Default: True
    Returns:     Array: Returns an array of env values objects.

    Example:
    # Get all of properties
    >>> Env.get_properties()
    # Get the properties in group 10
    >>> Env.get_properties(10)
    """
    query = {'is_active': parse_bool_value(is_active)}
    if env_property_id:
        query['property__pk'] = env_property_id

    return TCMSEnvValue.to_xmlrpc(query)
