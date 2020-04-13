from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^new/$', views.CreateTestRunView.as_view(), name='testruns-new'),
    url(r'^(?P<pk>\d+)/$', views.GetTestRunView.as_view(), name='testruns-get'),
    url(r'^(?P<pk>\d+)/clone/$', views.CloneTestRunView.as_view(), name='testruns-clone'),
    url(r'^(?P<pk>\d+)/edit/$', views.EditTestRunView.as_view(), name='testruns-edit'),

    url(r'^(?P<pk>\d+)/changestatus/$', views.ChangeTestRunStatusView.as_view(),
        name='testruns-change_status'),

    url(r'^(?P<pk>\d+)/update/$', views.UpdateCaseRunTextView.as_view(),
        name='testruns-update_case_run_text'),
    url(r'^update-assignee/$', views.UpdateAssigneeView.as_view()),

    url(r'^search/$', views.SearchTestRunView.as_view(), name='testruns-search'),
]
