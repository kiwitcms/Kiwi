# -*- coding: utf-8 -*-

from django.conf.urls import url
from .. import views

urlpatterns = [
    url(r'^search/$', views.search, name='testruns-search'),
    url(r'^env_value/$', views.env_value, name='testruns-env_value'),
]
