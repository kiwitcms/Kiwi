# -*- coding: utf-8 -*-

import httplib
import os
import sys
import traceback

from functools import wraps
from xmlrpclib import Fault

import django
from django.conf import settings


__filters__ = ('wrap_exceptions',)


def _validate_config():
    if not hasattr(settings, 'XMLRPC_METHODS'):
        raise ImportError("Variable 'XMLRPC_METHODS' not set in settings.")


def _get_enable_apis():
    _validate_config()
    apis = list()
    for value in settings.XMLRPC_METHODS.itervalues():
        for api in value:
            apis.append(api[0])
    return apis


def _wrap_exceptions(module_name):
    """Load api list and wrap them with decorators

    """
    module = __import__(module_name, {}, {}, [""])
    funcs = getattr(module, '__all__', None)
    if not funcs:
        return

    for func in funcs:
        func = getattr(module, func, None)
        if callable(func):
            for api_filter in XMLRPC_API_FILTERS:
                func = api_filter(func)
            setattr(sys.modules[module.__name__], func.__name__, func)


def autowrap_xmlrpc_apis(path, package):
    """Auto load xmlrpc api, based on directory structure and XMLRPC_METHODS
    setting.

    It will load modules that were listed in XMLRPC_METHODS, and get __all__
    attribute of each module to collect api functions.

    Then wrap the apis with decorators in order(appearance order in
    __filters__) and replace them.

    Everything is done when import tcms.xmlrpc.* or tcms.xmlrpc automatically.

    If you want to add new decorators, please append it in this module and
    insert it into __filters__.
    """
    our_dir = path[0]
    enable_apis = _get_enable_apis()
    for dir_path, dir_names, file_names in os.walk(our_dir):
        rel_path = os.path.relpath(dir_path, our_dir)
        if rel_path == '.':
            rel_pkg = ''
        else:
            rel_pkg = '.%s' % '.'.join(rel_path.split(os.sep))

        for file_name in file_names:
            root, ext = os.path.splitext(file_name)

            # Skip __init__ and anything that's not .py
            # FIXME maybe .pyc in prod env.
            if ext != '.py' or root == '__init__':
                continue

            module_name = ("%s%s.%s" %
                           (package, rel_pkg, root))

            if module_name in enable_apis:
                _wrap_exceptions(module_name)


def _format_message(msg):
    return [msg] if isinstance(msg, basestring) else msg


# create your own filter here.
def wrap_exceptions(func):
    @wraps(func)
    def _decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except django.core.exceptions.PermissionDenied as e:
            # 403 Forbidden
            fault_code = httplib.FORBIDDEN
            fault_string = str(e)
        except django.db.models.ObjectDoesNotExist as e:
            # 404 Not Found
            fault_code = httplib.NOT_FOUND
            fault_string = str(e)
        except (django.db.models.FieldDoesNotExist,
                django.core.exceptions.FieldError,
                django.core.exceptions.ValidationError,
                django.core.exceptions.MultipleObjectsReturned,
                ValueError,
                TypeError) as e:
            # 400 Bad Request
            fault_code = httplib.BAD_REQUEST
            fault_string = str(e)
        except django.db.utils.IntegrityError as e:
            # 409 Duplicate
            fault_code = httplib.CONFLICT
            fault_string = str(e)
        except NotImplementedError as e:
            fault_code = httplib.NOT_IMPLEMENTED
            fault_string = str(e)
        except Exception as e:
            # 500 Server Error
            fault_code = httplib.INTERNAL_SERVER_ERROR
            fault_string = str(e)

        if settings.DEBUG:
            stack_trace = ''.join(traceback.format_exception(*sys.exc_info()))
            fault_string = '%s\n%s' % (fault_string, stack_trace)

        raise Fault(faultCode=fault_code,
                    faultString=_format_message(fault_string))

    return _decorator


XMLRPC_API_FILTERS = [getattr(sys.modules[__name__], api_filter, None) for
                      api_filter in __filters__]
