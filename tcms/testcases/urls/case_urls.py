# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^(?P<case_id>\d+)/$', views.get, name='testcases-get'),
    url(r'^(?P<case_id>\d+)/edit/$', views.edit, name='testcases-edit'),
    url(r'^(?P<case_id>\d+)/history/$', views.text_history, name='testcases-text_history'),
    url(r'^(?P<case_id>\d+)/attachment/$', views.attachment, name='testcases-attachment'),
    url(r'^(?P<case_id>\d+)/bug/$', views.bug, name='testcases-bug'),
    url(r'^(?P<case_id>\d+)/plan/$', views.case_plan, name='testcases-plan'),
    url(r'^(?P<case_id>\d+)/readonly-pane/$', views.SimpleTestCaseView.as_view(),
        name='case-readonly-pane'),
    url(r'^(?P<case_id>\d+)/caserun-list-pane/$', views.TestCaseCaseRunListPaneView.as_view(),
        name='caserun-list-pane'),
    url(r'^(?P<case_id>\d+)/caserun-simple-pane/$', views.TestCaseSimpleCaseRunView.as_view(),
        name='caserun-simple-pane'),
    url(r'^(?P<case_id>\d+)/caserun-detail-pane/$', views.TestCaseCaseRunDetailPanelView.as_view(),
        name='caserun-detail-pane'),
]
