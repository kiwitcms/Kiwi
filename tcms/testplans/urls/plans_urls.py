# -*- coding: utf-8 -*-

from django.conf.urls import url
from .. import views

urlpatterns = [
    url(r'^$', views.all, name='plans-all'),
    # for compatibility with with core.views.search.search()
    url(r'^$', views.all, name='testplans-all'),

    url(r'^new/$', views.new, name='plans-new'),
    url(r'^ajax/$', views.ajax_search),
    url(r'^treeview/$', views.tree_view),
    url(r'^clone/$', views.clone, name='plans-clone'),
    url(r'^printable/$', views.printable, name='plans-printable'),
    url(r'^export/$', views.export, name='plans-export'),
    url(r'^component/$', views.component),
]
