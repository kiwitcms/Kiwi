# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^$', views.all, name='runs-all'),
    url(r'^ajax/$', views.ajax_search, name='runs-ajax-search'),
    url(r'^env_value/$', views.env_value, name='runs-env-value'),
    url(r'^clone/$', views.clone, name='runs-clone'),
]
