# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

from tcms.testcases.views import SimpleTestCaseView
from tcms.testcases.views import TestCaseCaseRunDetailPanelView
from tcms.testcases.views import TestCaseCaseRunListPaneView
from tcms.testcases.views import TestCaseReviewPaneView
from tcms.testcases.views import TestCaseSimpleCaseRunView

urlpatterns = patterns(
    'tcms.testcases.views',
    url(r'^(?P<case_id>\d+)/$', 'get'),
    url(r'^(?P<case_id>\d+)/edit/$', 'edit'),
    url(r'^(?P<case_id>\d+)/history/$', 'text_history'),
    url(r'^(?P<case_id>\d+)/attachment/$', 'attachment'),
    url(r'^(?P<case_id>\d+)/log/$', 'get_log'),
    url(r'^(?P<case_id>\d+)/bug/$', 'bug'),
    url(r'^(?P<case_id>\d+)/plan/$', 'plan'),
    url(r'^(?P<case_id>\d+)/readonly-pane/$', SimpleTestCaseView.as_view(),
        name='case-readonly-pane'),
    url(r'^(?P<case_id>\d+)/review-pane/$', TestCaseReviewPaneView.as_view(),
        name='case-review-pane'),
    url(r'^(?P<case_id>\d+)/caserun-list-pane/$', TestCaseCaseRunListPaneView.as_view(),
        name='caserun-list-pane'),
    url(r'^(?P<case_id>\d+)/caserun-simple-pane/$', TestCaseSimpleCaseRunView.as_view(),
        name='caserun-simple-pane'),
    url(r'^(?P<case_id>\d+)/caserun-detail-pane/$', TestCaseCaseRunDetailPanelView.as_view(),
        name='caserun-detail-pane'),
)


urlpatterns += patterns(
    'tcms.testruns.views',
    url(r'^(?P<plan_id>\d+)/runs/$', 'load_runs_of_one_plan',
        name='load_runs_of_one_plan_url'),
)
