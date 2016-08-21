# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

urlpatterns = patterns(
    'tcms.testplans.views',
    url(r'^(?P<plan_id>\d+)/$', 'get', name='test_plan_url'),
    url(r'^(?P<plan_id>\d+)/(?P<slug>[-\w\d]+)$', 'get', name='test_plan_url'),
    url(r'^(?P<plan_id>\d+)/delete/$', 'delete'),
    url(r'^(?P<plan_id>\d+)/chooseruns/$', 'choose_run'),
    url(r'^(?P<plan_id>\d+)/edit/$', 'edit'),
    url(r'^(?P<plan_id>\d+)/attachment/$', 'attachment'),
    url(r'^(?P<plan_id>\d+)/history/$', 'text_history'),
    url(r'^(?P<plan_id>\d+)/cases/$', 'cases'),
)

urlpatterns += patterns(
    'tcms.testruns.views',
    url(r'^(?P<plan_id>\d+)/runs/$', 'load_runs_of_one_plan',
        name='load_runs_of_one_plan_url'),
)
