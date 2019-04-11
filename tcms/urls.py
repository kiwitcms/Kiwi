# -*- coding: utf-8 -*-
import pkg_resources
from importlib import import_module

from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.i18n import JavaScriptCatalog

from grappelli import urls as grappelli_urls
from attachments import urls as attachments_urls
from modernrpc.core import JSONRPC_PROTOCOL
from modernrpc.core import XMLRPC_PROTOCOL
from modernrpc.views import RPCEntryPoint
from tcms.core import ajax
from tcms.core import views as core_views
from tcms.core.contrib.comments import views as comments_views
from tcms.core.contrib.linkreference import views as linkreference_views
from tcms.testplans import urls as testplans_urls
from tcms.testcases import urls as testcases_urls
from tcms.kiwi_auth import urls as auth_urls
from tcms.testruns import urls as testruns_urls
from tcms.telemetry import urls as telemetry_urls


urlpatterns = [
    url(r'^$', core_views.dashboard, name='core-views-index'),
    url(r'^xml-rpc/', RPCEntryPoint.as_view(protocol=XMLRPC_PROTOCOL)),
    url(r'^json-rpc/$', RPCEntryPoint.as_view(protocol=JSONRPC_PROTOCOL)),
    url(r'^navigation/', core_views.navigation, name='iframe-navigation'),

    url(r'^grappelli/', include(grappelli_urls)),
    url(r'^admin/', admin.site.urls),

    url(r'^attachments/', include(attachments_urls, namespace='attachments')),

    # Ajax call responder
    url(r'^ajax/update/cases-actor/$', ajax.UpdateTestCaseActorsView.as_view(),
        name='ajax.update.cases-actor'),
    url(r'^management/tags/$', ajax.tags, name='ajax-tags'),

    # comments
    url(r'^comments/post/', comments_views.post, name='comments-post'),
    url(r'^comments/delete/', comments_views.delete, name='comments-delete'),

    # Account information zone, such as login method
    url(r'^accounts/', include(auth_urls)),

    # Testplans zone
    url(r'^plan/', include(testplans_urls.plan_urls)),
    url(r'^plans/', include(testplans_urls.plans_urls)),

    # Testcases zone
    url(r'^case/', include(testcases_urls.case_urls)),
    url(r'^cases/', include(testcases_urls.cases_urls)),

    # Testruns zone
    url(r'^runs/', include(testruns_urls)),

    url(r'^telemetry/', include(telemetry_urls)),

    url(r'^caserun/comment-many/', ajax.comment_case_runs, name='ajax-comment_case_runs'),
    url(r'^caserun/update-bugs-for-many/', ajax.update_bugs_to_caseruns),

    url(r'^linkref/add/$', linkreference_views.add, name='linkref-add'),
    url(r'^linkref/remove/(?P<link_id>\d+)/$', linkreference_views.remove),

    # JavaScript translations, see
    # https://docs.djangoproject.com/en/2.1/topics/i18n/translation/#django.views.i18n.JavaScriptCatalog
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]


for plugin in pkg_resources.iter_entry_points('kiwitcms.telemetry.plugins'):
    plugin_urls = import_module('%s.urls' % plugin.module_name)
    urlpatterns.append(
        url(r'^%s/' % plugin.name, include(plugin_urls))
    )


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns.extend([
        url(r'^500/$', TemplateView.as_view(template_name="500.html")),
        url(r'^404/$', TemplateView.as_view(template_name="404.html")),
    ])

    try:
        import debug_toolbar

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
    # in case we're trying to debug in production
    # and debug_toolbar is not installed
    except ImportError:
        pass


# Overwrite default 500 handler
# More details could see django.core.urlresolvers._resolve_special()
handler500 = 'tcms.core.views.server_error'
