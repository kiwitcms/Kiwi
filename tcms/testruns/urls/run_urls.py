# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.new, name='testruns-new'),
    url(r'^(?P<run_id>\d+)/$', views.get, name='testruns-get'),
    url(r'^(?P<run_id>\d+)/clone/$', views.new_run_with_caseruns,
        name='testruns-clone-with-caseruns'),
    url(r'^(?P<run_id>\d+)/delete/$', views.delete, name='testruns-delete'),
    url(r'^(?P<run_id>\d+)/edit/$', views.edit, name='testruns-edit'),

    url(r'^(?P<run_id>\d+)/report/$', views.TestRunReportView.as_view(),
        name='run-report'),

    url(r'^(?P<run_id>\d+)/ordercase/$', views.order_case),
    url(r'^(?P<run_id>\d+)/changestatus/$', views.change_status, name='testruns-change_status'),
    url(r'^(?P<run_id>\d+)/ordercaserun/$', views.order_case, name='testruns-order_case'),
    url(r'^(?P<run_id>\d+)/removecaserun/$', views.remove_case_run,
        name='testruns-remove_case_run'),

    url(r'^(?P<run_id>\d+)/assigncase/$', views.AddCasesToRunView.as_view(),
        name='add-cases-to-run'),

    url(r'^(?P<run_id>\d+)/cc/$', views.cc, name='testruns-cc'),
    url(r'^(?P<run_id>\d+)/update/$', views.update_case_run_text,
        name='testruns-update_case_run_text'),
]
