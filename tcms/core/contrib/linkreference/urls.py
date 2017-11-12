# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^add/$', views.add),
    url(r'^get/$', views.get),
    url(r'^remove/(?P<link_id>\d+)/$', views.remove),
]
