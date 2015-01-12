# -*- coding: utf-8 -*-

from django.conf.urls import url, patterns

urlpatterns = patterns(
    'tcms.testruns.views',
    url(r'^$', 'all'),
    url(r'^ajax/$', 'ajax_search'),
    url(r'^env_value/$', 'env_value'),
    url(r'^clone/$', 'clone'),
)
