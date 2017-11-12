# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.new, name='run-new'),
    url(r'^(?P<run_id>\d+)/$', views.get, name='run-get'),
    url(r'^(?P<run_id>\d+)/clone/$', views.new_run_with_caseruns, name='run-clone'),
    url(r'^(?P<run_id>\d+)/delete/$', views.delete, name='run-delete'),
    url(r'^(?P<run_id>\d+)/edit/$', views.edit, name='run-edit'),

    url(r'^(?P<run_id>\d+)/report/$', views.TestRunReportView.as_view(),
        name='run-report'),

    url(r'^(?P<run_id>\d+)/ordercase/$', views.order_case, name='run-order-case'),
    url(r'^(?P<run_id>\d+)/changestatus/$', views.change_status, name='run-change-status'),
    url(r'^(?P<run_id>\d+)/ordercaserun/$', views.order_case, name='run-order-caserun'),
    url(r'^(?P<run_id>\d+)/removecaserun/$', views.remove_case_run, name='run-remove-caserun'),

    url(r'^(?P<run_id>\d+)/assigncase/$', views.AddCasesToRunView.as_view(),
        name='add-cases-to-run'),

    url(r'^(?P<run_id>\d+)/cc/$', views.cc, name='run-cc'),
    url(r'^(?P<run_id>\d+)/update/$', views.update_case_run_text, name='run-update'),
    url(r'^(?P<run_id>\d+)/export/$', views.export, name='run-export'),
]
