# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.admindocs import urls as admindocs_urls
from django.views.i18n import JavaScriptCatalog

from tinymce import urls as tinymce_urls
from tcms.core import ajax
from tcms.core import files
from tcms.core import views as core_views
from tcms.core.contrib.comments import views as comments_views
from tcms.core.contrib.linkreference import views as linkreference_views
from tcms.profiles import urls as profiles_urls
from tcms.testplans import urls as testplans_urls
from tcms.testcases import urls as testcases_urls
from tcms.testruns import urls as testruns_urls
from tcms.testruns import views as testruns_views
from tcms.management import views as management_views
from tcms.report import urls as report_urls
from tcms.search import advance_search
from tcms.xmlrpc import urls as xmlrpc_urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^admin/doc/', include(admindocs_urls)),

    url(r'^tinymce/', include(tinymce_urls)),

    # Index and static zone
    url(r'^$', core_views.index, name='core-views-index'),
    url(r'^search/$', core_views.search, name='core-views-search'),
    url(r'^xmlrpc/', include(xmlrpc_urls)),

    # Ajax call responder
    url(r'^ajax/update/$', ajax.update, name='ajax-update'),
    url(r'^ajax/update/case-status/$', ajax.update_cases_case_status),
    url(r'^ajax/update/case-run-status$', ajax.update_case_run_status, name='ajax-update_case_run_status'),
    url(r'^ajax/update/cases-priority/$', ajax.update_cases_priority),
    url(r'^ajax/update/cases-default-tester/$', ajax.update_cases_default_tester,
        name='ajax-update_cases_default_tester'),
    url(r'^ajax/update/cases-reviewer/$', ajax.update_cases_reviewer),
    url(r'^ajax/update/cases-sortkey/$', ajax.update_cases_sortkey),
    url(r'^ajax/form/$', ajax.form, name='ajax-form'),
    url(r'^ajax/get-prod-relate-obj/$', ajax.get_prod_related_obj_json),
    url(r'^management/getinfo/$', ajax.info, name='ajax-info'),
    url(r'^management/tags/$', ajax.tag),

    # Attached file zone
    url(r'^management/uploadfile/$', files.upload_file, name='mgmt-upload_file'),
    url(r'^management/checkfile/(?P<file_id>\d+)/$', files.check_file, name='mgmt-check_file'),
    url(r'^management/deletefile/(?P<file_id>\d+)/$', files.delete_file, name='mgmt-delete_file'),

    # comments
    url(r'^comments/post/', comments_views.post, name='comments-post'),
    url(r'^comments/delete/', comments_views.delete, name='comments-delete'),

    # Account information zone, such as login method
    url(r'^accounts/', include(profiles_urls)),

    # Testplans zone
    url(r'^plan/', include(testplans_urls.plan_urls)),
    url(r'^plans/', include(testplans_urls.plans_urls)),

    # Testcases zone
    url(r'^case/', include(testcases_urls.case_urls)),
    url(r'^cases/', include(testcases_urls.cases_urls)),

    # Testruns zone
    url(r'^run/', include(testruns_urls.run_urls)),
    url(r'^runs/', include(testruns_urls.runs_urls)),

    url(r'^caseruns/$', testruns_views.caseruns),
    url(r'^caserun/(?P<case_run_id>\d+)/bug/$', testruns_views.bug, name='testruns-bug'),
    url(r'^caserun/comment-many/', ajax.comment_case_runs, name='ajax-comment_case_runs'),
    url(r'^caserun/update-bugs-for-many/', ajax.update_bugs_to_caseruns),

    url(r'^linkref/add/$', linkreference_views.add),
    url(r'^linkref/get/$', linkreference_views.get),
    url(r'^linkref/remove/(?P<link_id>\d+)/$', linkreference_views.remove),

    # Management zone
    url(r'^environment/groups/$', management_views.environment_groups,
        name='mgmt-environment_groups'),
    url(r'^environment/group/edit/$', management_views.environment_group_edit,
        name='mgmt-environment_group_edit'),
    url(r'^environment/properties/$', management_views.environment_properties,
        name='mgmt-environment_properties'),
    url(r'^environment/properties/values/$', management_views.environment_property_values,
        name='mgmt-environment_property_values'),

    # Report zone
    url(r'^report/', include(report_urls)),

    # Advance search
    url(r'^advance-search/$', advance_search, name='advance_search'),

    # TODO: do we need this at all ???
    # Using admin js without admin permission
    # https://docs.djangoproject.com/en/1.11/topics/i18n/translation/#django.views.i18n.JavaScriptCatalog
    url(r'^jsi18n/$', JavaScriptCatalog.as_view()),
]

# Debug zone

if settings.DEBUG:
    try:
        import debug_toolbar
        from tcms.core.utils import test_template

        urlpatterns += [
            url(r'^__debug__/', include(debug_toolbar.urls)),
            url(r'^tt/(?P<template_name>.*)', test_template.test_template),
        ]
    # in case we're trying to debug in production
    # and debug_toolbar is not installed
    except ImportError:
        pass

# Overwrite default 500 handler
# More details could see django.core.urlresolvers._resolve_special()
handler500 = 'tcms.core.views.error.server_error'
