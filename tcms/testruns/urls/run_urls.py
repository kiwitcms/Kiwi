# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.new),
    url(r'^(?P<run_id>\d+)/$', views.get),
    url(r'^(?P<run_id>\d+)/clone/$', views.new_run_with_caseruns),
    url(r'^(?P<run_id>\d+)/delete/$', views.delete),
    url(r'^(?P<run_id>\d+)/edit/$', views.edit),

    url(r'^(?P<run_id>\d+)/report/$', views.TestRunReportView.as_view(),
        name='run-report'),

    url(r'^(?P<run_id>\d+)/ordercase/$', views.order_case),
    url(r'^(?P<run_id>\d+)/changestatus/$', views.change_status),
    url(r'^(?P<run_id>\d+)/ordercaserun/$', views.order_case),
    url(r'^(?P<run_id>\d+)/removecaserun/$', views.remove_case_run),

    url(r'^(?P<run_id>\d+)/assigncase/$', views.AddCasesToRunView.as_view(),
        name='add-cases-to-run'),

    url(r'^(?P<run_id>\d+)/cc/$', views.cc),
    url(r'^(?P<run_id>\d+)/update/$', views.update_case_run_text),
    url(r'^(?P<run_id>\d+)/export/$', views.export),
]
