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
