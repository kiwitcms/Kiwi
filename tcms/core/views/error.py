from django import http
from django.template import (RequestContext, loader, TemplateDoesNotExist)
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def server_error(request, template_name='500.html'):
    """Django default handler renders the template with an empty
    RequestContext, and worse, the static file with prefix 'STATIC_URL' will
    become a relative resource on current page,

    e.g:
    http://host/run/118632/images/logo_shipshape_1.png

    Here we render the error page with request object which has 'STATIC_URL'
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseServerError('<h1>Server Error (500)</h1>')
    return http.HttpResponseServerError(
        template.render(RequestContext(request)))
