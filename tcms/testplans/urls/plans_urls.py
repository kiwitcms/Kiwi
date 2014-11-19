# -*- coding: utf-8 -*-

from django.conf.urls import include, url, patterns

urlpatterns = patterns('tcms.testplans.views',
    url(r'^$', 'all'),
    url(r'^new/$', 'new'),
    url(r'^ajax/$', 'ajax_search'),
    url(r'^treeview/$', 'tree_view'),
    url(r'^clone/$', 'clone'),
    url(r'^printable/$', 'printable'),
    url(r'^export/$', 'export'),
    url(r'^component/$', 'component'),
)
