# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url

from .. import views
from tcms.testruns import views as testruns_views

urlpatterns = [
    url(r'^(?P<plan_id>\d+)/$', views.get, name='plan-get'),
    url(r'^(?P<plan_id>\d+)/(?P<slug>[-\w\d]+)$', views.get, name='plan-get'),
    url(r'^(?P<plan_id>\d+)/delete/$', views.delete, name='plan-delete'),
    url(r'^(?P<plan_id>\d+)/chooseruns/$', views.choose_run, name='plan-choose-run'),
    url(r'^(?P<plan_id>\d+)/edit/$', views.edit, name='plan-edit'),
    url(r'^(?P<plan_id>\d+)/attachment/$', views.attachment, name='plan-attachment'),
    url(r'^(?P<plan_id>\d+)/history/$', views.text_history, name='plan-text-history'),
    url(r'^(?P<plan_id>\d+)/cases/$', views.cases, name='plan-cases'),

    url(r'^(?P<plan_id>\d+)/runs/$', testruns_views.load_runs_of_one_plan,
        name='load_runs_of_one_plan_url'),
]
