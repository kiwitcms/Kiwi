# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', views.TestCaseGetView.as_view(), name='testcases-get'),
    url(r'^(?P<pk>\d+)/edit/$', views.EditTestCaseView.as_view(), name='testcases-edit'),
    url(r'^(?P<case_id>\d+)/readonly-pane/$', views.SimpleTestCaseView.as_view(),
        name='case-readonly-pane'),
    url(r'^(?P<case_id>\d+)/execution-detail-pane/$',
        views.TestCaseExecutionDetailPanelView.as_view(),
        name='execution-detail-pane'),
]
