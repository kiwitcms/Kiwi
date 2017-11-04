# -*- coding: utf-8 -*-

from django.conf.urls import include, url, patterns

urlpatterns = patterns('tcms.profiles.views',
    url(r'^profile/$', 'redirect_to_profile'),
    url(r'^(?P<username>[\w.@+-]+)/profile/$', 'profile'),
    url(r'^(?P<username>[\w.@+-]+)/bookmarks/$', 'bookmark'),
    url(r'^(?P<username>[\w.@+-]+)/recent/$', 'recent'),
)

urlpatterns += patterns('tcms.core.contrib.auth.views',
    url(r'logout/$', 'logout'),
    url(r'register/$', 'register'),
    url(r'confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$', 'confirm'),
)

urlpatterns += patterns('django.contrib.auth.views',
    url(r'login/$', 'login'),
    url(r'changepassword/$', 'password_change', name='password_change'),
    url(r'changepassword/done/$', 'password_change_done', name='password_change_done'),
    url(r'^passwordreset/$', 'password_reset', name='password_reset'),
    url(r'^passwordreset/done/$', 'password_reset_done', name='password_reset_done'),
    url(r'^passwordreset/confirm//(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'password_reset_confirm', name='password_reset_confirm'),
)
