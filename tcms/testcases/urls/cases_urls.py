# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.conf.urls import url
from .. import views

urlpatterns = [
    url(r'^new/$', views.new, name='cases-new'),
    url(r'^$', views.all, name='cases-all'),
    url(r'^search/$', views.search, name='cases-search'),
    url(r'^load-more/$', views.load_more_cases, name='cases-load-more'),
    url(r'^ajax/$', views.ajax_search, name='cases-ajax-search'),
    url(r'^automated/$', views.automated, name='cases-automated'),
    url(r'^tag/$', views.tag, name='cases-tag'),
    url(r'^category/$', views.category, name='cases-category'),
    url(r'^clone/$', views.clone, name='cases-clone'),
    url(r'^printable/$', views.printable, name='cases-printable'),
    url(r'^export/$', views.export, name='cases-export'),

    url(r'^add-component/$', views.AddComponentView.as_view(),
        name='cases-add-component'),
    url(r'^remove-component/$', views.RemoveComponentView.as_view(),
        name='cases-remove-component'),
    url(r'^get-component-form/$', views.GetComponentFormView.as_view(),
        name='cases-get-component-form'),
]
