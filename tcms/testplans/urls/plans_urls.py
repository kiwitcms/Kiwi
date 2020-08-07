# -*- coding: utf-8 -*-

from django.urls import re_path

from tcms.testplans import views

urlpatterns = [
    re_path(r'^search/$', views.SearchTestPlanView.as_view(), name='plans-search'),
    re_path(r'^new/$', views.NewTestPlanView.as_view(), name='plans-new'),
    re_path(r'^clone/$', views.Clone.as_view(), name='plans-clone'),
    re_path(r'^printable/$', views.printable, name='plans-printable'),
]
