# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url
from . import ajax, files, views

urlpatterns = [
    # Site entry
    url(r'^$', views.index, name='nitrate-index'),
    url(r'^search/$', views.search, name='nitrate-search'),

    # Ajax call responder
    url(r'^ajax/update/$', ajax.update, name='ajax-update'),

    # TODO: merge this into next mapping
    url(r'^ajax/update/case-status/$', ajax.update_cases_case_status),
    url(r'^ajax/update/case-run-status$', ajax.update_case_run_status,
        name='ajax-update-caserun-status'),
    url(r'^ajax/update/cases-priority/$', ajax.update_cases_priority),
    url(r'^ajax/update/cases-default-tester/$', ajax.update_cases_default_tester,
        name='ajax-update-cases-default-tester'),
    url(r'^ajax/update/cases-reviewer/$', ajax.update_cases_reviewer),
    url(r'^ajax/update/cases-sortkey/$', ajax.update_cases_sortkey),
    url(r'^ajax/form/$', ajax.form, name='ajax-form'),
    url(r'^ajax/get-prod-relate-obj/$', ajax.get_prod_related_obj_json),
    url(r'^management/getinfo/$', ajax.info, name='ajax-getinfo'),
    url(r'^management/tags/$', ajax.tag),

    # Attached file zone
    url(r'^management/uploadfile/$', files.upload_file, name='upload-file'),
    url(r'^management/checkfile/(?P<file_id>\d+)/$', files.check_file,
        name='check-file'),
    url(r'^management/deletefile/(?P<file_id>\d+)/$', files.delete_file,
        name='delete-file'),
]
