# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.sites.models import Site

from tcms.core.utils import request_host_link


class UrlMixin:  # pylint: disable=too-few-public-methods
    """Mixin class for getting full URL"""

    def get_full_url(self):
        site = Site.objects.get(pk=settings.SITE_ID)
        host_link = request_host_link(None, site.domain)
        _absolute_url = self._get_absolute_url().strip("/")
        return f"{host_link}/{_absolute_url}/"
