# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views
from tcms.testruns.views import load_runs_of_one_plan

urlpatterns = [
    url(r'^(?P<plan_id>\d+)/$', views.get, name='test_plan_url'),
    url(r'^(?P<plan_id>\d+)/(?P<slug>[-\w\d]+)$', views.get, name='test_plan_url'),
    url(r'^(?P<plan_id>\d+)/delete/$', views.delete),
    url(r'^(?P<plan_id>\d+)/chooseruns/$', views.choose_run),
    url(r'^(?P<plan_id>\d+)/edit/$', views.edit),
    url(r'^(?P<plan_id>\d+)/attachment/$', views.attachment),
    url(r'^(?P<plan_id>\d+)/history/$', views.text_history),
    url(r'^(?P<plan_id>\d+)/cases/$', views.cases),

    url(r'^(?P<plan_id>\d+)/runs/$', load_runs_of_one_plan, name='load_runs_of_one_plan_url')
]
