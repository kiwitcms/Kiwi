# -*- coding: utf-8 -*-

from django.conf.urls import url
from .. import views

urlpatterns = [
    url(r'^$', views.all),
    url(r'^new/$', views.new),
    url(r'^ajax/$', views.ajax_search),
    url(r'^treeview/$', views.tree_view),
    url(r'^clone/$', views.clone),
    url(r'^printable/$', views.printable),
    url(r'^export/$', views.export),
    url(r'^component/$', views.component),
]
