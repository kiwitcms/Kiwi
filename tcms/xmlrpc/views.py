# -*- coding: utf-8 -*-


# Based on http://code.djangoproject.com/wiki/XML-RPC
#
# Credits:
#        Brendan W. McAdams


"""
USAGE:
Add following structure to your Django settings file:
XMLRPC_TEMPLATE = "xmlrpc.html"
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
from django.template import Template, RequestContext, loader

from .dispatcher import DjangoXMLRPCDispatcher


# this has to be list, since new handlers are appended when the module is loaded
__all__ = []


XMLRPC_TEMPLATE = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
  <meta http-equiv="Content-Language" content="en-us" />
  <meta name="robots" content="NONE,NOARCHIVE" />
  <title>XML-RPC Service</title>
</head>

<body style="font-size: small;">
  <h2>This is an XML-RPC Service</h2>
  You need to invoke it using an XML-RPC Client!<br />

  <h2>Available methods</h2>
  <ul>
  {% for method in method_list %}
    <li><a href="#{{ method.name|lower }}">{{ method.name|escape }}</a></li>
  {% endfor %}
  </ul>

  <h2>Details</h2>
  {% for method in method_list %}
    <h3><a name="{{ method.name|lower }}">{{ method.name|escape }}</a></h3>
    {% ifnotequal method.signature "signatures not supported" %}<strong>Signature: </strong>{{ method.signature|escape }}<br />{% endifnotequal %}
    <pre>{% for line in method.help %}{{ line|escape }}<br />{% endfor %}</pre>
  {% endfor %}
</body>
</html>
"""


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
            except ImportError, ex:
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
                method_list.append({
                    "name": method,
                    "signature": self.xmlrpc_dispatcher.system_methodSignature(method),
                    "help": self.xmlrpc_dispatcher.system_methodHelp(method).split("\n"),
                })

            c = RequestContext(request, {
                "title": "XML-RPC interface (%s)" % self.name,
                "method_list": method_list,
            })

            template = getattr(settings, "XMLRPC_TEMPLATE", None)
            if template is not None:
                t = loader.get_template(template)
            else:
                t = Template(XMLRPC_TEMPLATE, name="XML-RPC template")

            context_instance = RequestContext(request)
            context_instance.update(c)
            return HttpResponse(t.render(context_instance))


for var in ("XMLRPC_METHODS", ):
    if not hasattr(settings, var):
        raise ImproperlyConfigured("Variable '%s' not set in settings." % var)


for i in settings.XMLRPC_METHODS.iterkeys():
    XMLRPCHandlerFactory(i)
