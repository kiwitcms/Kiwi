# -*- coding: utf-8 -*-
from django.core.cache import cache
from modernrpc.auth.basic import http_basic_auth_login_required
from modernrpc.core import rpc_method

from tcms.core.templatetags.extra_filters import markdown2html

__all__ = ("render",)


@http_basic_auth_login_required
@rpc_method(name="Markdown.render")
def render(text):
    """
    .. function:: RPC Markdown.render(text)

        Returns the input string rendered into HTML with all the filters
        and extensions available in markdown2html().

        Note: when used via the front-end all of the HTML tags will be
        escaped eventhough they are safe to use! The FE client should
        unescape them in case this HTML is to be shown on the screen!

        :param text: Markdown text
        :type text: str
        :return: Rendered HTML text
        :rtype: str
    """
    result = cache.get(text)
    if result:
        return result

    result = markdown2html(text)
    cache.set(text, result)
    return result
