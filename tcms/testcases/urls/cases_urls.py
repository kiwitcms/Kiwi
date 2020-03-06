# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.NewCaseView.as_view(), name='testcases-new'),
    url(r'^search/$', views.TestCaseSearchView.as_view(), name='testcases-search'),
    url(r'^clone/$', views.CloneTestCaseView.as_view(), name='testcases-clone'),
]
