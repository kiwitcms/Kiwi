# -*- coding: utf-8 -*-

import inspect
import logging
from functools import wraps
from django.conf import settings
from django.contrib.auth import get_user_model


__all__ = ('log_call',)

logger = logging.getLogger('kiwi.xmlrpc')

if settings.DEBUG:
    # To avoid pollute XMLRPC logs with those generated during development
    def create_log(user, method, args):
        log_msg = 'user: {0}, method: {1}, args: {2}'.format(
            user.username if hasattr(user, 'username') else user,
            method,
            args)
        logger.debug(log_msg)
else:
    from .models import XmlRpcLog
    create_log = XmlRpcLog.objects.create


def log_call(*args, **kwargs):
    '''Log XMLRPC-specific invocations

    This was copied from kobo.django.xmlrpc.decorators to add custom abitlities,
    so that we don't have to wait upstream to make the changes.

    Usage::

        from tcms.core.decorators import log_call
        @log_call(namespace='TestNamespace')
        def func(request):
            return None
    '''
    namespace = kwargs.get('namespace', '')
    if namespace:
        namespace = namespace + '.'

    def decorator(function):
        argspec = inspect.getargspec(function)
        # Each XMLRPC method has an HttpRequest argument as the first one,
        # it'll be ignored in the log.
        arg_names = argspec.args[1:]

        @wraps(function)
        def _new_function(request, *args, **kwargs):
            try:
                known_args = list(zip(arg_names, args))
                unknown_args = list(enumerate(args[len(arg_names):]))
                keyword_args = [(key, value) for key, value in
                                kwargs.items()
                                if (key, value) not in known_args]
                request_user = request.user
                if not request_user.is_authenticated:
                    # create an anonymous 'User' object for XML-RPC logging
                    # purposes !
                    request_user, _ = get_user_model().objects.get_or_create(
                        username='Anonymous',
                        is_active=False)
                create_log(user=request_user,
                           method='%s%s' % (namespace, function.__name__),
                           args=str(known_args + unknown_args + keyword_args))
            except Exception:
                pass
            return function(request, *args, **kwargs)

        return _new_function

    return decorator
