# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', views.Get.as_view(), name='bugs-get'),
    url(r'^new/$', views.New.as_view(), name='bugs-new'),
    url(r'^(?P<pk>\d+)/edit/$', views.Edit.as_view(), name='bugs-edit'),
    url(r'^search/$', views.Search.as_view(), name='bugs-search'),
    url(r'^comment/$', views.AddComment.as_view(), name='bugs-comment'),
]
