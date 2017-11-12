# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url
from .. import views

urlpatterns = [
    url(r'^$', views.all, name='plans-all'),
    url(r'^new/$', views.new, name='plans-new'),
    url(r'^ajax/$', views.ajax_search, name='plans-ajax-search'),
    url(r'^treeview/$', views.tree_view, name='plans-treeview'),
    url(r'^clone/$', views.clone, name='plans-clone'),
    url(r'^printable/$', views.printable, name='plans-printable'),
    url(r'^export/$', views.export, name='plans-export'),
    url(r'^component/$', views.component, name='plans-component'),
]
