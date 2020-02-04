# -*- coding: utf-8 -*-

from django.conf.urls import url

from tcms.testplans import views

urlpatterns = [
    url(r'^search/$', views.SearchTestPlanView.as_view(), name='plans-search'),
    url(r'^new/$', views.NewTestPlanView.as_view(), name='plans-new'),
    url(r'^clone/$', views.Clone.as_view(), name='plans-clone'),
    url(r'^printable/$', views.printable, name='plans-printable'),
]
