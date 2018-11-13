# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.new, name='testcases-new'),
    url(r'^$', views.all, name='testcases-all'),
    url(r'^search/$', views.search, name='testcases-search'),
    url(r'^load-more/$', views.load_more_cases),
    url(r'^clone/$', views.clone, name='testcases-clone'),
    url(r'^printable/$', views.printable, name='testcases-printable'),
]
