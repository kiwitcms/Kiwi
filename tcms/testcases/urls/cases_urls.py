# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.new, name='testcases-new'),
    url(r'^$', views.all, name='testcases-all'),
    url(r'^search/$', views.search, name='testcases-search'),
    url(r'^load-more/$', views.load_more_cases),
    url(r'^ajax/$', views.ajax_search, name='testcases-ajax_search'),
    url(r'^automated/$', views.automated, name='testcases-automated'),
    url(r'^tag/$', views.tag, name='testcases-tag'),
    url(r'^component/$', views.component, name='testcases-component'),
    url(r'^category/$', views.category, name='testcases-category'),
    url(r'^clone/$', views.clone, name='testcases-clone'),
    url(r'^printable/$', views.printable, name='testcases-printable'),
    url(r'^export/$', views.export, name='testcases-export'),
]
