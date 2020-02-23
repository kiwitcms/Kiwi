# -*- coding: utf-8 -*-

from django.conf.urls import url

from tcms.testplans import views

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', views.GetTestPlanRedirectView.as_view(), name='test_plan_url_short'),
    # human friendly url
    url(r'^(?P<pk>\d+)/(?P<slug>[-\w\d]+)$', views.TestPlanGetView.as_view(),
        name='test_plan_url'),

    url(r'^(?P<pk>\d+)/edit/$', views.Edit.as_view(), name='plan-edit'),

    url(r'^(?P<pk>\d+)/reorder-cases/$', views.ReorderCasesView.as_view(),
        name='plan-reorder-cases'),
    url(r'^update-parent/$', views.UpdateParentView.as_view()),
]
