# pylint: disable=no-self-use, too-few-public-methods

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class CheckDBStructureExistsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path == "/init-db/":
            return None
        try:
            Site.objects.get(pk=settings.SITE_ID)
        except (OperationalError, ProgrammingError):
            # Redirect to Setup view
            return HttpResponseRedirect(reverse("init-db"))
        return None
