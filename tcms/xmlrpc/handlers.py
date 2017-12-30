# -*- coding: utf-8 -*-

import logging
from modernrpc import handlers

from django.conf import settings
from django.contrib.auth import get_user_model

from .models import XmlRpcLog

__all__ = ['XMLRPCHandler', 'JSONRPCHandler']
logger = logging.getLogger('kiwi.xmlrpc')


def log_call(request, method_name, args):
    """
        Log an RPC call to the database or stdout in debug mode.
    """
    # avoid logging passwords sent via RPC
    if method_name in ['Auth.login', 'User.update']:
        args = ''

    # if passing arguments via dicts and one of the keys is named "password"
    # also serves as fallback in case we've missed to blacklist a method above
    if 'password' in str(args).lower():
        args = ''

    request_user = request.user
    if not request_user.is_authenticated:
        # create an anonymous 'User' object for XML-RPC logging purposes !
        request_user, _ = get_user_model().objects.get_or_create(
            username='Anonymous',
            is_active=False)

    if method_name is None:
        method_name = '--- method_name missing ---'

    if settings.DEBUG:
        # To avoid polluting XMLRPC logs with those generated during development
        log_msg = 'user: {0}, method: {1}, args: {2}'.format(
            request_user.username if hasattr(request_user, 'username') else request_user,
            method_name, args)
        logger.debug(log_msg)
    else:
        XmlRpcLog.objects.create(
            user=request_user,
            method=method_name,
            args=str(args))


class XMLRPCHandler(handlers.XMLRPCHandler):
    def process_request(self):
        encoding = self.request.encoding or 'utf-8'
        data = self.request.body.decode(encoding)
        params, method_name = self.loads(data)

        log_call(self.request, method_name, params)
        return super(XMLRPCHandler, self).process_request()


class JSONRPCHandler(handlers.JSONRPCHandler):
    def process_single_request(self, payload):
        method_name = payload.get('method', None)
        params = payload.get('params')

        log_call(self.request, method_name, params)
        return super(JSONRPCHandler, self).process_single_request(payload)
