# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

from tcms.testruns.views import TestRunReportView
from tcms.testruns.views import AddCasesToRunView

urlpatterns = patterns(
    'tcms.testruns.views',
    url(r'^new/$', 'new'),
    url(r'^(?P<run_id>\d+)/$', 'get'),
    url(r'^(?P<run_id>\d+)/clone/$', 'new_run_with_caseruns'),
    url(r'^(?P<run_id>\d+)/delete/$', 'delete'),
    url(r'^(?P<run_id>\d+)/edit/$', 'edit'),

    url(r'^(?P<run_id>\d+)/report/$',
        TestRunReportView.as_view(),
        name='run-report'),

    url(r'^(?P<run_id>\d+)/ordercase/$', 'order_case'),
    url(r'^(?P<run_id>\d+)/changestatus/$', 'change_status'),
    url(r'^(?P<run_id>\d+)/ordercaserun/$', 'order_case'),
    url(r'^(?P<run_id>\d+)/removecaserun/$', 'remove_case_run'),

    url(r'^(?P<run_id>\d+)/assigncase/$',
        AddCasesToRunView.as_view(),
        name='add-cases-to-run'),

    url(r'^(?P<run_id>\d+)/cc/$', 'cc'),
    url(r'^(?P<run_id>\d+)/update/$', 'update_case_run_text'),
    url(r'^(?P<run_id>\d+)/export/$', 'export'),
)
