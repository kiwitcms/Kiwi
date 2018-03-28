# -*- coding: utf-8 -*-

from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_backend(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i + 1:]
    try:
        mod = import_module(module)
    except ImportError as err:
        raise ImproperlyConfigured(
            'Error loading registration backend %s: "%s"' % (module, err)
        )
    try:
        backend_class = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured(
            'Module "%s" does not define a registration '
            'backend named "%s"' % (module, attr)
        )
    return backend_class()


def get_using_backend():
    return get_backend(settings.AUTHENTICATION_BACKENDS[0])
