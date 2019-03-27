# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^(?P<case_id>\d+)/$', views.get, name='testcases-get'),
    url(r'^(?P<case_id>\d+)/edit/$', views.edit, name='testcases-edit'),
    url(r'^(?P<case_id>\d+)/attachment/$', views.attachment, name='testcases-attachment'),
    url(r'^(?P<case_id>\d+)/readonly-pane/$', views.SimpleTestCaseView.as_view(),
        name='case-readonly-pane'),
    url(r'^(?P<case_id>\d+)/caserun-detail-pane/$', views.TestCaseCaseRunDetailPanelView.as_view(),
        name='caserun-detail-pane'),
]
