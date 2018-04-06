# -*- coding: utf-8 -*-

from django.conf.urls import url
from .. import views

urlpatterns = [
    url(r'^$', views.get_all, name='plans-all'),
    url(r'^new/$', views.new, name='plans-new'),
    url(r'^ajax/$', views.ajax_search, name='plans-ajax_search'),
    url(r'^clone/$', views.clone, name='plans-clone'),
    url(r'^printable/$', views.printable, name='plans-printable'),
]
