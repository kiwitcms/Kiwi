# pylint: disable=no-self-use, too-few-public-methods

from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _


class CsrfDisableMiddleware(MiddlewareMixin):
    def process_view(self, request, _callback, _callback_args, _callback_kwargs):
        setattr(request, '_dont_enforce_csrf_checks', True)


class CheckSettingsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        doc_url = 'https://kiwitcms.readthedocs.io/en/latest/admin.html#configure-kiwi-s-base-url'
        site = Site.objects.get(pk=settings.SITE_ID)

        if site.domain == '127.0.0.1:8000':
            messages.add_message(
                request,
                messages.ERROR,
                _('Base URL is not configured! '
                  'See <a href="%(doc_url)s">documentation</a> and '
                  '<a href="%(admin_url)s">change it</a>') % {
                      'doc_url': doc_url,
                      'admin_url': reverse('admin:sites_site_change', args=[site.pk])}
            )
