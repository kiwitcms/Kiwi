# -*- coding: utf-8 -*-

from django.conf.urls import url

from .. import views

urlpatterns = [
    url(r'^new/$', views.new),
    url(r'^$', views.all),
    url(r'^search/$', views.search),
    url(r'^load-more/$', views.load_more_cases),
    url(r'^ajax/$', views.ajax_search),
    url(r'^automated/$', views.automated),
    url(r'^tag/$', views.tag),
    url(r'^component/$', views.component),
    url(r'^category/$', views.category),
    url(r'^clone/$', views.clone),
    url(r'^printable/$', views.printable),
    url(r'^export/$', views.export),
]
