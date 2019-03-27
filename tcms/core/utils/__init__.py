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
