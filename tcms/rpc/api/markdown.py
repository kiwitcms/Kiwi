from django.core.cache import cache

from tcms.core.templatetags.extra_filters import markdown2html
from tcms.rpc.decorators import django_login_required
from tcms.rpc.views import rpc_method


@rpc_method(
    name="Markdown.render",
    auth=django_login_required,
)
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
