# -*- coding: utf-8 -*-

from tcms.management.models import TestTag
from tcms.xmlrpc.decorators import log_call

__all__ = ('get_tags', )

__xmlrpc_namespace__ = 'Tag'


@log_call(namespace=__xmlrpc_namespace__)
def get_tags(request, values):
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
    if values.get('ids'):
        query = {'id__in': values.get('ids')}
        return TestTag.to_xmlrpc(query)
    elif values.get('names'):
        query = {'name__in': values.get('names')}
        return TestTag.to_xmlrpc(query)
    else:
        raise ValueError('Must specify ids or names at least.')
