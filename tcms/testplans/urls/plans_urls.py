# -*- coding: utf-8 -*-

from django.conf.urls import url

from tcms.testplans import views

urlpatterns = [
    url(r'^search/$', views.SearchTestPlanView.as_view(), name='plans-search'),
    url(r'^new/$', views.NewTestPlanView.as_view(), name='plans-new'),
]
