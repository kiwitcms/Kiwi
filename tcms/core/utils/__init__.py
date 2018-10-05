# -*- coding: utf-8 -*-
#  pylint: disable=too-few-public-methods

import sys


def string_to_list(strs, spliter=','):
    """Convert the string to list"""
    if isinstance(strs, list):
        str_list = (str(item).strip() for item in strs)
    elif isinstance(strs, str) and strs.find(spliter):
        str_list = (str(item).strip() for item in strs.split(spliter))
    else:
        str_list = (strs,)

    lst = []
    for string in str_list:
        if string:
            lst.append(string)
    return lst


def form_errors_to_list(form):
    """
    Convert errors of form to list
    Use for Ajax.Request response
    """
    errors = []
    for key, value in form.errors.items():
        errors.append((key, value[0]))
    return errors


def request_host_link(request, domain_name=None):
    protocol = 'https://'
    if 'runserver' in sys.argv:
        protocol = 'http://'

    if request:
        if not domain_name:
            domain_name = request.get_host()
        # default to https if in production and we don't know
        protocol = 'https://'
        if not request.is_secure():
            protocol = 'http://'

    return protocol + domain_name


# todo: remove this
def clean_request(request, keys=None):
    """
    Clean the request strings
    """
    request_contents = request.GET.copy()
    if not keys:
        keys = request_contents.keys()
    cleaned_request = {}
    for key in keys:
        key = str(key)
        if request_contents.get(key):
            if key in ('order_by', 'from_plan'):
                continue

            value = request.GET[key]
            # Convert the value to be list if it's __in filter.
            if key.endswith('__in') and isinstance(value, str):
                value = string_to_list(value)
            cleaned_request[key] = value
    return cleaned_request


class QuerySetIterationProxy:
    """Iterate a series of object and its associated objects at once

    This iteration proxy applies to this kind of structure especially.

    Group       Properties          Logs
    -------------------------------------------------
    group 1     property 1          log at Mon.
                property 2          log at Tue.
                property 3          log at Wed.
    -------------------------------------------------
    group 2     property 4          log at Mon.
                property 5          log at Tue.
                property 6          log at Wed.
    -------------------------------------------------
    group 3     property 7          log at Mon.
                property 8          log at Tue.
                property 9          log at Wed.

    where, in each row of the table, one or more than one properties and logs
    to be shown along with the group.
    """

    def __init__(self, iterable, associate_name=None, **associated_data):
        """Initialize proxy

        Arguments:
        - iterable: an iterable object representing the main set of objects.
        - associate_name: the attribute name of each object within iterable,
          from which value is retrieve to get associated data from
          associate_data. Default is 'pk'.
        - associate_data: the associated data, that contains all data for each
          item in the set referenced by iterable. You can pass mulitple
          associated data as the way of Python **kwargs. The associated data
          must be grouped by the value of associate_name.
        """
        self._iterable = iter(iterable)
        self._associate_name = associate_name
        if self._associate_name is None:
            self._associate_name = 'pk'
        self._associated_data = associated_data

    def __iter__(self):
        return self

    def __next__(self):
        next_one = next(self._iterable)
        for name, lookup_table in self._associated_data.items():
            setattr(next_one,
                    name,
                    lookup_table.get(
                        getattr(next_one, self._associate_name, None),
                        ()))
        return next_one
