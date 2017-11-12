# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.views.i18n import JavaScriptCatalog

from tcms.testruns import views as testruns_views
from tcms.core import ajax as tcms_core_ajax

# XML RPC handler
from kobo.django.xmlrpc.views import XMLRPCHandlerFactory
xmlrpc_handler = XMLRPCHandlerFactory('TCMS_XML_RPC')

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'', include('tcms.core.urls')),
    url(r'', include('tcms.management.urls')),

    # Testplans zone
    url(r'^plan/', include('tcms.testplans.urls.plan_urls')),
    url(r'^plans/', include('tcms.testplans.urls.plans_urls')),

    # Testcases zone
    url(r'^case/', include('tcms.testcases.urls.case_urls')),
    url(r'^cases/', include('tcms.testcases.urls.cases_urls')),

    # Testruns zone
    url(r'^run/', include('tcms.testruns.urls.run_urls')),
    url(r'^runs/', include('tcms.testruns.urls.runs_urls')),

    url(r'^caseruns/$', testruns_views.caseruns),
    url(r'^caserun/(?P<case_run_id>\d+)/bug/$', testruns_views.bug,
        name='caserun-bug'),
    url(r'^caserun/comment-many/', tcms_core_ajax.comment_case_runs,
        name='caserun-comment-caseruns'),
    url(r'^caserun/update-bugs-for-many/',
        tcms_core_ajax.update_bugs_to_caseruns),

    url(r'^accounts/', include('tcms.profiles.urls')),
    url(r'^linkref/', include('tcms.core.contrib.linkreference.urls')),
    url(r'^comments/', include('tcms.core.contrib.comments.urls')),
    url(r'^advance-search/', include('tcms.search.urls')),
    url(r'^report/', include('tcms.report.urls')),
    url(r'^xmlrpc/$', xmlrpc_handler),
    url(r'^tinymce/', include('tinymce.urls')),

    # Using admin js without admin permission
    # refer: https://docs.djangoproject.com/en/1.6/topics/i18n/translation/#module-django.views.i18n
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
]

# Debug zone

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

# Overwrite default 500 handler
# More details could see django.core.urlresolvers._resolve_special()
handler500 = 'tcms.core.views.error.server_error'
