# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib.auth import views as contrib_auth_views

from . import views as profiles_views
from tcms.core.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^profile/$', profiles_views.redirect_to_profile),
    url(r'^(?P<username>[\w.@+-]+)/profile/$', profiles_views.profile),
    url(r'^(?P<username>[\w.@+-]+)/bookmarks/$', profiles_views.bookmark),
    url(r'^(?P<username>[\w.@+-]+)/recent/$', profiles_views.recent),

    url(r'logout/$', auth_views.logout),
    url(r'register/$', auth_views.register),
    url(r'confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$', auth_views.confirm),

    url(r'login/$', contrib_auth_views.login),
    url(r'changepassword/$', contrib_auth_views.password_change),
    url(r'changepassword/done/$', contrib_auth_views.password_change_done),
    url(r'^passwordreset/$', contrib_auth_views.password_reset),
    url(r'^passwordreset/done/$', contrib_auth_views.password_reset_done),
    url(r'^passwordreset/confirm//(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        contrib_auth_views.password_reset_confirm),
]
