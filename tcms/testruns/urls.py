from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^new/$', views.CreateTestRunView.as_view(), name='testruns-new'),
    url(r'^(?P<run_id>\d+)/$', views.GetTestRunView.as_view(), name='testruns-get'),
    url(r'^(?P<run_id>\d+)/clone/$', views.CloneTestRunView.as_view(), name='testruns-clone'),
    url(r'^(?P<pk>\d+)/edit/$', views.EditTestRunView.as_view(), name='testruns-edit'),

    url(r'^(?P<run_id>\d+)/report/$', views.TestRunReportView.as_view(),
        name='run-report'),

    url(r'^(?P<run_id>\d+)/changestatus/$', views.ChangeTestRunStatusView.as_view(),
        name='testruns-change_status'),

    url(r'^(?P<run_id>\d+)/assigncase/$', views.AddCasesToRunView.as_view(),
        name='add-cases-to-run'),

    url(r'^(?P<run_id>\d+)/cc/$', views.ManageTestRunCC.as_view(), name='testruns-cc'),
    url(r'^(?P<run_id>\d+)/update/$', views.UpdateCaseRunTextView.as_view(),
        name='testruns-update_case_run_text'),
    url(r'^update-assignee/$', views.UpdateAssigneeView.as_view()),
    url(r'^case-run-update-status/$', views.UpdateCaseRunStatusView.as_view(),
        name='testruns-update_caserun_status'),

    url(r'^search/$', views.SearchTestRunView.as_view(), name='testruns-search'),
]
