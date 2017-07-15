# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib.auth import views as contrib_auth_views

from . import views as profiles_views
from tcms.core.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^profile/$', profiles_views.redirect_to_profile, name='tcms-redirect_to_profile'),
    url(r'^(?P<username>[\w.@+-]+)/profile/$', profiles_views.profile,
        name='tcms-profile'),
    url(r'^(?P<username>[\w.@+-]+)/bookmarks/$', profiles_views.bookmark,
        name='tcms-bookmark'),
    url(r'^(?P<username>[\w.@+-]+)/recent/$', profiles_views.recent,
        name='tcms-recent'),

    url(r'logout/$', auth_views.logout, name='tcms-logout'),
    url(r'register/$', auth_views.register, name='tcms-register'),
    url(r'confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$', auth_views.confirm,
        name='tcms-confirm'),

    url(r'login/$', contrib_auth_views.login, name='tcms-login'),
    url(r'changepassword/$', contrib_auth_views.password_change, name='tcms-password_change'),
    url(r'changepassword/done/$', contrib_auth_views.password_change_done),
    url(r'^passwordreset/$', contrib_auth_views.password_reset, name='tcms-password_reset'),
    url(r'^passwordreset/done/$', contrib_auth_views.password_reset_done),
    url(r'^passwordreset/confirm//(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        contrib_auth_views.password_reset_confirm),
]
