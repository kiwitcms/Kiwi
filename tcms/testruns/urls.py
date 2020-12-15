from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^new/$", views.NewTestRunView.as_view(), name="testruns-new"),
    re_path(r"^(?P<pk>\d+)/$", views.GetTestRunView.as_view(), name="testruns-get"),
    re_path(
        r"^(?P<pk>\d+)/clone/$", views.CloneTestRunView.as_view(), name="testruns-clone"
    ),
    re_path(
        r"^(?P<pk>\d+)/edit/$", views.EditTestRunView.as_view(), name="testruns-edit"
    ),
    re_path(r"^search/$", views.SearchTestRunView.as_view(), name="testruns-search"),
]
