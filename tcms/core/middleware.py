# pylint: disable=no-self-use, too-few-public-methods

from django.conf import settings
from django.contrib import messages
from django.contrib.sites.models import Site
from django.db import DEFAULT_DB_ALIAS, connections
from django.db.migrations.executor import MigrationExecutor
from django.db.utils import OperationalError, ProgrammingError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


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


class CheckSettingsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        doc_url = "https://kiwitcms.readthedocs.io/en/latest/admin.html#configure-kiwi-s-base-url"
        if request.path == "/init-db/":
            return
        site = Site.objects.get(pk=settings.SITE_ID)

        if site.domain == "127.0.0.1:8000":
            messages.add_message(
                request,
                messages.ERROR,
                mark_safe(  # nosec:B308:B703
                    _(
                        "Base URL is not configured! "
                        'See <a href="%(doc_url)s">documentation</a> and '
                        '<a href="%(admin_url)s">change it</a>'
                    )
                    % {
                        "doc_url": doc_url,
                        "admin_url": reverse("admin:sites_site_change", args=[site.pk]),
                    }
                ),
            )


class CheckUnappliedMigrationsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.path == "/init-db/":
            return
        doc_url = (
            "https://kiwitcms.readthedocs.io/en/latest/"
            "installing_docker.html#initial-configuration-of-running-container"
        )
        executor = MigrationExecutor(connections[DEFAULT_DB_ALIAS])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            messages.add_message(
                request,
                messages.ERROR,
                mark_safe(  # nosec:B308:B703
                    _(
                        "You have %(unapplied_migration_count)s unapplied migration(s). "
                        'See <a href="%(doc_url)s">documentation</a>'
                    )
                    % {
                        "unapplied_migration_count": len(plan),
                        "doc_url": doc_url,
                    }
                ),
            )
