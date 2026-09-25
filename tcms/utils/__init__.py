# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme


def save_referer_redirect(request):
    referer = request.META.get("HTTP_REFERER", "/")
    if url_has_allowed_host_and_scheme(
        url=referer,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return HttpResponseRedirect(referer)
    return HttpResponseRedirect("/")
