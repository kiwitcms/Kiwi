# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import TestTag

__all__ = ('get_tags', )


@rpc_method(name='Tag.get_tags')
def get_tags(values):
    """
    Description:  Get the list of tags.

    Params:      $values - Hash: keys must match valid search fields.
        +------------------------------------------------------------+
        |                   tag Search Parameters                    |
        +------------------------------------------------------------+
        | Key                     | Valid Values                     |
        | ids                     | List of Integer                  |
        | names                   | List of String                   |
        +------------------------------------------------------------+

    Returns:     Array: An array of tag object hashes.

    Example:

    >>> values= {'ids': [121, 123]}
    >>> Tag.get_tags(values)
    """
    if not isinstance(values, dict):
        raise TypeError('Argument values must be a dictionary.')

    if values.get('ids'):
        query = {'id__in': values.get('ids')}
        return TestTag.to_xmlrpc(query)
    elif values.get('names'):
        query = {'name__in': values.get('names')}
        return TestTag.to_xmlrpc(query)
    else:
        raise ValueError('Must specify ids or names at least.')
