# -*- coding: utf-8 -*-

from django.urls import re_path

from .. import views

urlpatterns = [
    re_path(r"^new/$", views.NewCaseView.as_view(), name="testcases-new"),
    re_path(r"^search/$", views.TestCaseSearchView.as_view(), name="testcases-search"),
    re_path(r"^clone/$", views.CloneTestCaseView.as_view(), name="testcases-clone"),
]
