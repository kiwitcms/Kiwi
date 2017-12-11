# -*- coding: utf-8 -*-


# Based on http://code.djangoproject.com/wiki/XML-RPC
#
# Credits:
#        Brendan W. McAdams


"""
USAGE:
Add following structure to your Django settings file:
XMLRPC_METHODS = {
    'xmlrpc1': (
        ('module.xmlrpc.method', 'exported_name'),
        ('module.xmlrpc.module', 'module_prefix'),
    ),
    'xmlrpc2': (
        ...
    ),
}

<key>_handler method is created for each key in XMLRPC_METHODS
(xmlrpc1_handler and xmlrpc2_handler in this case).

It is encouraged to use __all__ when exporting whole module.

All double underscores in method names will be replaced with dots:
def task__create(request, ...): will be registered as task.create(...)
"""

import sys

import django.db
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse

from .dispatcher import DjangoXMLRPCDispatcher


# this has to be list, since new handlers are appended when the module is loaded
__all__ = []


class XMLRPCHandlerFactory(object):
    def __call__(self, request):
        return self.xmlrpc_handler(request)

    def __init__(self, name):
        self.name = name
        # xml-rpc must be excluded from CSRF processing
        # instances of this class are being passed to CSRF middleware
        self.csrf_exempt = True
        self.xmlrpc_dispatcher = DjangoXMLRPCDispatcher(allow_none=True, encoding=None)
        self.setup_dispatcher()
        self.register()

    def setup_dispatcher(self):
        for path, name in settings.XMLRPC_METHODS[self.name]:
            # *path* is a function, register it as *name*
            if callable(path):
                self.xmlrpc_dispatcher.register_function(path, name)
                continue

            # *path* is a module, register all functions inside and use *name* as a prefix
            try:
                module = __import__(path, {}, {}, [""])
                self.xmlrpc_dispatcher.register_module(module, name)
                continue
            except ImportError:
                pass

            if path.count(".") == 0:
                raise ImproperlyConfigured("Error registering XML-RPC method: '%s' must be one of (function, 'module' or 'module.function')" % path)

            # try to find callable function
            module_name, fn = path.rsplit(".", 1)

            try:
                module = __import__(module_name, {}, {}, [fn])
            except ImportError as ex:
                raise ImproperlyConfigured("Error registering XML-RPC method: module '%s' cannot be imported: %s" % (module_name, ex))

            try:
                func = getattr(module, fn)
            except AttributeError:
                raise ImproperlyConfigured("Error registering XML-RPC method: module '%s' doesn't define function '%s'" % (module, fn))

            if not callable(func):
                raise ImproperlyConfigured("Error registering XML-RPC method: '%s' is not callable in module '%s'" % (fn, module_name))

            # *path* is a module.function, register it as *name*
            self.xmlrpc_dispatcher.register_function(func, name)

    def register(self):
        # inject this instance to current module
        handler_name = "%s_handler" % self.name
        setattr(sys.modules[__name__], handler_name, self)
        sys.modules[__name__].__all__.append(handler_name)

    def xmlrpc_handler(self, request):
        if settings.DEBUG:
            # clear queries to stop django allocating more and more memory
            # http://docs.djangoproject.com/en/dev/faq/models/#why-is-django-leaking-memory
            django.db.reset_queries()

        if request.method == "POST":
            return HttpResponse(self.xmlrpc_dispatcher._marshaled_dispatch(request), content_type="text/xml")
        else:
            method_list = []
            for method in self.xmlrpc_dispatcher.system_listMethods():
                method_list.append(method)

            return HttpResponse("\n".join(method_list),
                                content_type="text/plain")


for var in ("XMLRPC_METHODS", ):
    if not hasattr(settings, var):
        raise ImproperlyConfigured("Variable '%s' not set in settings." % var)


for i in settings.XMLRPC_METHODS.keys():
    XMLRPCHandlerFactory(i)
