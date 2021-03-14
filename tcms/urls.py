# -*- coding: utf-8 -*-
from importlib import import_module

import pkg_resources
from attachments import urls as attachments_urls
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import re_path
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog
from grappelli import urls as grappelli_urls
from modernrpc.core import JSONRPC_PROTOCOL, XMLRPC_PROTOCOL
from modernrpc.views import RPCEntryPoint

from tcms.core import views as core_views
from tcms.kiwi_auth import urls as auth_urls
from tcms.telemetry import urls as telemetry_urls
from tcms.testcases import urls as testcases_urls
from tcms.testplans import urls as testplans_urls
from tcms.testruns import urls as testruns_urls

urlpatterns = [
    re_path(r"^$", core_views.DashboardView.as_view(), name="core-views-index"),
    re_path(r"^xml-rpc/", RPCEntryPoint.as_view(protocol=XMLRPC_PROTOCOL)),
    re_path(r"^json-rpc/$", RPCEntryPoint.as_view(protocol=JSONRPC_PROTOCOL)),
    re_path(r"^init-db/$", core_views.InitDBView.as_view(), name="init-db"),
    re_path(
        r"^translation-mode/",
        core_views.TranslationMode.as_view(),
        name="translation-mode",
    ),
    re_path(r"^grappelli/", include(grappelli_urls)),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^attachments/", include(attachments_urls, namespace="attachments")),
    # Account information zone, such as login method
    re_path(r"^accounts/", include(auth_urls)),
    # Testplans zone
    re_path(r"^plan/", include(testplans_urls)),
    # Testcases zone
    re_path(r"^case/", include(testcases_urls.case_urls)),
    re_path(r"^cases/", include(testcases_urls.cases_urls)),
    # Testruns zone
    re_path(r"^runs/", include(testruns_urls)),
    re_path(r"^telemetry/", include(telemetry_urls)),
    # JavaScript translations, see
    # https://docs.djangoproject.com/en/2.1/topics/i18n/translation/#django.views.i18n.JavaScriptCatalog
    re_path(r"^jsi18n/$", JavaScriptCatalog.as_view(), name="javascript-catalog"),
]


# conditional import b/c this App can be disabled
if "tcms.bugs.apps.AppConfig" in settings.INSTALLED_APPS:
    from tcms.bugs import urls as bugs_urls

    urlpatterns.append(re_path(r"^bugs/", include(bugs_urls)))


for plugin in pkg_resources.iter_entry_points("kiwitcms.plugins"):
    plugin_urls = import_module("%s.urls" % plugin.module_name)
    urlpatterns.append(re_path(r"^%s/" % plugin.name, include(plugin_urls)))


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns.extend(
        [
            re_path(r"^500/$", TemplateView.as_view(template_name="500.html")),
            re_path(r"^404/$", TemplateView.as_view(template_name="404.html")),
        ]
    )

    try:
        import debug_toolbar

        urlpatterns += [
            re_path(r"^__debug__/", include(debug_toolbar.urls)),
        ]
    # in case we're trying to debug in production
    # and debug_toolbar is not installed
    except ImportError:
        pass


# Overwrite default 500 handler
# More details could see django.core.urlresolvers._resolve_special()
handler500 = "tcms.core.views.server_error"
