# -*- coding: utf-8 -*-

from django.conf.urls import url

from tcms.testplans import views
from tcms.testruns.views import load_runs_of_one_plan

urlpatterns = [
    url(r'^(?P<plan_id>\d+)/$', views.get, name='test_plan_url_short'),
    # human friendly url
    url(r'^(?P<plan_id>\d+)/(?P<slug>[-\w\d]+)$', views.get, name='test_plan_url'),

    url(r'^(?P<plan_id>\d+)/chooseruns/$', views.choose_run, name='plan-choose_run'),
    url(r'^(?P<plan_id>\d+)/edit/$', views.edit, name='plan-edit'),
    url(r'^(?P<plan_id>\d+)/attachment/$', views.attachment, name='plan-attachment'),

    url(r'^(?P<plan_id>\d+)/reorder-cases/$', views.ReorderCasesView.as_view(),
        name='plan-reorder-cases'),
    url(r'^(?P<plan_id>\d+)/link-cases/$', views.LinkCasesView.as_view(),
        name='plan-link-cases'),
    url(r'^(?P<plan_id>\d+)/link-cases/search/$', views.LinkCasesSearchView.as_view(),
        name='plan-search-cases-for-link'),
    url(r'^(?P<plan_id>\d+)/delete-cases/$', views.DeleteCasesView.as_view(),
        name='plan-delete-cases'),

    url(r'^(?P<plan_id>\d+)/runs/$', load_runs_of_one_plan, name='load_runs_of_one_plan_url'),
    url(r'^update-parent/$', views.UpdateParentView.as_view()),
]
