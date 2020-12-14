# -*- coding: utf-8 -*-

from django.urls import re_path

from .. import views

urlpatterns = [
    re_path(r"^(?P<pk>\d+)/$", views.TestCaseGetView.as_view(), name="testcases-get"),
    re_path(
        r"^(?P<pk>\d+)/edit/$", views.EditTestCaseView.as_view(), name="testcases-edit"
    ),
]
