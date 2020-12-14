# Copyright (c) 2019-2020 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^(?P<pk>\d+)/$", views.Get.as_view(), name="bugs-get"),
    re_path(r"^new/$", views.New.as_view(), name="bugs-new"),
    re_path(r"^(?P<pk>\d+)/edit/$", views.Edit.as_view(), name="bugs-edit"),
    re_path(r"^search/$", views.Search.as_view(), name="bugs-search"),
    re_path(r"^comment/$", views.AddComment.as_view(), name="bugs-comment"),
]
