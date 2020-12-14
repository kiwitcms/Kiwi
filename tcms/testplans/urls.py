# -*- coding: utf-8 -*-

from django.urls import re_path

from tcms.testplans import views

urlpatterns = [
    re_path(
        r"^(?P<pk>\d+)/$",
        views.GetTestPlanRedirectView.as_view(),
        name="test_plan_url_short",
    ),
    # human friendly url
    re_path(
        r"^(?P<pk>\d+)/(?P<slug>[-\w\d]+)$",
        views.TestPlanGetView.as_view(),
        name="test_plan_url",
    ),
    re_path(r"^(?P<pk>\d+)/edit/$", views.Edit.as_view(), name="plan-edit"),
    re_path(r"^(?P<pk>\d+)/clone/$", views.Clone.as_view(), name="plans-clone"),
    re_path(r"^search/$", views.SearchTestPlanView.as_view(), name="plans-search"),
    re_path(r"^new/$", views.NewTestPlanView.as_view(), name="plans-new"),
]
