from django.db.models.query import QuerySet
from django.http import HttpRequest


def remove_from_request_path(request, name):
    """
    Remove a parameter from request.get_full_path()\n
    and return the modified path afterwards.
    """
    if isinstance(request, HttpRequest):
        path = request.get_full_path()
    else:
        path = request
    path = path.split('?')
    if len(path) > 1:
        path = path[1].split('&')
    else:
        return None

    for parameter in path:
        if parameter.startswith(name):
            path.remove(parameter)

    path = '&'.join(path)
    return '?' + path


def fmt_queries(*queries):
    """
    Format the queries string.
    """
    results = {}
    for _query in queries:
        for key, value in _query.items():
            key = replace_keys(key)
            if isinstance(value, bool) or value:
                if isinstance(value, QuerySet):
                    try:
                        value = ', '.join(o.name for o in value)
                    except AttributeError:
                        try:
                            value = ', '.join(o.value for o in value)
                        except AttributeError:
                            value = ', '.join(value)
                if isinstance(value, list):
                    value = ', '.join(map(str, value))
                results[key] = value
    return results


def replace_keys(key):
    key = key.replace('p_product', 'product')
    key = key.replace('p_', 'product ')
    key = key.replace('cs_', 'case ')
    key = key.replace('pl_', 'plan ')
    key = key.replace('r_', 'run ')
    return key.replace('_', ' ')
