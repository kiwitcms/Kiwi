# -*- coding: utf-8 -*-

from django.conf.urls import include, url, patterns

urlpatterns = patterns('tcms.testcases.views',
    url(r'^new/$', 'new'),
    url(r'^$', 'all'),
    url(r'^search/$', 'search'),
    url(r'^load-more/$', 'load_more_cases'),
    url(r'^ajax/$', 'ajax_search'),
    url(r'^automated/$', 'automated'),
    url(r'^tag/$', 'tag'),
    url(r'^component/$', 'component'),
    url(r'^category/$', 'category'),
    url(r'^clone/$', 'clone'),
    url(r'^printable/$', 'printable'),
    url(r'^export/$', 'export'),
)
