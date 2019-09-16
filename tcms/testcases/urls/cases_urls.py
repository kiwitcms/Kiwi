# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.NewCaseView.as_view(), name='testcases-new'),
    url(r'^$', views.list_all, name='testcases-all'),
    url(r'^search/$', views.TestCaseSearchView.as_view(), name='testcases-search'),
    url(r'^load-more/$', views.load_more_cases),
    url(r'^clone/$', views.CloneTestCaseView.as_view(), name='testcases-clone'),
    url(r'^printable/$', views.printable, name='testcases-printable'),
]
