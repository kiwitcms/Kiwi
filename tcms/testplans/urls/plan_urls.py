# -*- coding: utf-8 -*-

from django.urls import re_path

from tcms.testplans import views

urlpatterns = [
    re_path(r'^(?P<pk>\d+)/$', views.GetTestPlanRedirectView.as_view(), name='test_plan_url_short'),
    # human friendly url
    re_path(r'^(?P<pk>\d+)/(?P<slug>[-\w\d]+)$', views.TestPlanGetView.as_view(),
            name='test_plan_url'),

    re_path(r'^(?P<pk>\d+)/edit/$', views.Edit.as_view(), name='plan-edit'),

    re_path(r'^(?P<pk>\d+)/reorder-cases/$', views.ReorderCasesView.as_view(),
            name='plan-reorder-cases'),
    re_path(r'^(?P<pk>\d+)/link-cases/$', views.LinkCasesView.as_view(),
            name='plan-link-cases'),
    re_path(r'^(?P<pk>\d+)/link-cases/search/$', views.LinkCasesSearchView.as_view(),
            name='plan-search-cases-for-link'),
    re_path(r'^update-parent/$', views.UpdateParentView.as_view()),
]
