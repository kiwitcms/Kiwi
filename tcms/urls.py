# -*- coding: utf-8 -*-

import os
from django.conf import settings
from django.conf.urls import include, url, patterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# XML RPC handler
from kobo.django.xmlrpc.views import XMLRPCHandlerFactory
xmlrpc_handler = XMLRPCHandlerFactory('TCMS_XML_RPC')

urlpatterns = patterns('',
    # Example:
    # (r'^tcms/', include('tcms.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),

    # tinymce
    (r'^tinymce/', include('tinymce.urls')),

    # Index and static zone
    (r'^$', 'tcms.core.views.index'),
    (r'^search/$', 'tcms.core.views.search'),
    (r'^xmlrpc/$', xmlrpc_handler),

    # Ajax call responder
    (r'^ajax/update/$', 'tcms.core.ajax.update'),
    # TODO: merge this into next mapping
    (r'^ajax/update/case-status$', 'tcms.core.ajax.update_case_status'),
    (r'^ajax/update/cases-case-status/$', 'tcms.core.ajax.update_cases_case_status'),
    (r'^ajax/update/case-run-status$', 'tcms.core.ajax.update_case_run_status'),
    (r'^ajax/update/cases-priority/$', 'tcms.core.ajax.update_cases_priority'),
    (r'^ajax/update/cases-default-tester/$', 'tcms.core.ajax.update_cases_default_tester'),
    (r'^ajax/update/cases-reviewer/$', 'tcms.core.ajax.update_cases_reviewer'),
    (r'^ajax/update/cases-sortkey/$', 'tcms.core.ajax.update_cases_sortkey'),
    (r'^ajax/form/$', 'tcms.core.ajax.form'),
    (r'^ajax/get-prod-relate-obj/$', 'tcms.core.ajax.get_prod_related_obj_json'),
    (r'^management/getinfo/$', 'tcms.core.ajax.info'),
    (r'^management/tags/$', 'tcms.core.ajax.tag'),

    # Attached file zone
    (r'^management/uploadfile/$', 'tcms.core.files.upload_file'),
    (r'^management/checkfile/(?P<file_id>\d+)/$', 'tcms.core.files.check_file'),
    (r'^management/deletefile/(?P<file_id>\d+)/$', 'tcms.core.files.delete_file'),

    (r'^comments/post/', 'tcms.core.contrib.comments.views.post'),
    (r'^comments/list/', 'tcms.core.contrib.comments.views.all'),
    (r'^comments/delete/', 'tcms.core.contrib.comments.views.delete'),

    # Account information zone, such as login method
    url(r'^accounts/', include('tcms.profiles.urls')),

    # Testplans zone
    url(r'^plan/', include('tcms.testplans.urls.plan_urls')),
    url(r'^plans/', include('tcms.testplans.urls.plans_urls')),

    # Testcases zone
    url(r'^case/', include('tcms.testcases.urls.case_urls')),
    url(r'^cases/', include('tcms.testcases.urls.cases_urls')),

    # Testruns zone
    url(r'^run/', include('tcms.testruns.urls.run_urls')),
    url(r'^runs/', include('tcms.testruns.urls.runs_urls')),

    (r'^caseruns/$', 'tcms.testruns.views.caseruns'),
    (r'^caserun/(?P<case_run_id>\d+)/bug/$', 'tcms.testruns.views.bug'),
    (r'^caserun/comment-many/', 'tcms.core.ajax.comment_case_runs'),
    (r'^caserun/update-bugs-for-many/', 'tcms.core.ajax.update_bugs_to_caseruns'),

    (r'^linkref/add/$', 'tcms.core.contrib.linkreference.views.add'),
    (r'^linkref/get/$', 'tcms.core.contrib.linkreference.views.get'),
    (r'^linkref/remove/(?P<link_id>\d+)/$', 'tcms.core.contrib.linkreference.views.remove'),

    # Management zone
    # (r'^management/$', 'tcms.management.views.index'),
    (r'^environment/groups/$', 'tcms.management.views.environment_groups'),
    (r'^environment/group/edit/$', 'tcms.management.views.environment_group_edit'),
    (r'^environment/properties/$', 'tcms.management.views.environment_properties'),
    (r'^environment/properties/values/$', 'tcms.management.views.environment_property_values'),

    # Management ajax zone

    # Report zone
    url(r'^report/', include('tcms.report.urls')),

    # Advance search
    url(r'^advance-search/$', 'tcms.search.advance_search', name='advance_search'),

    # Using admin js without admin permission
    # refer: https://docs.djangoproject.com/en/1.6/topics/i18n/translation/#module-django.views.i18n
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
     {'packages': ('django.conf', 'django.contrib.admin')}),
)

# Debug zone

if settings.DEBUG:
    urlpatterns += patterns(
        'tcms.core.utils.test_template',
        (r'^tt/(?P<template_name>.*)', 'test_template'),
    )

    if settings.STATIC_ROOT and os.path.exists(settings.STATIC_ROOT):
        from django.contrib.staticfiles.urls import staticfiles_urlpatterns
        urlpatterns += staticfiles_urlpatterns()

# Overwrite default 500 handler
# More details could see django.core.urlresolvers._resolve_special()
handler500 = 'tcms.core.views.error.server_error'
