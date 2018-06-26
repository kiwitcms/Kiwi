# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.urls import reverse_lazy
from django.contrib.auth import views as contrib_auth_views

from . import views as profiles_views
from tcms.core.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^(?P<username>[\w.@+-]+)/profile/$', profiles_views.profile,
        name='tcms-profile'),
    url(r'bookmarks/$', profiles_views.bookmarks, name='tcms-bookmarks'),
    url(r'dashboard/$', profiles_views.dashboard, name='tcms-dashboard'),

    url(r'^logout/$',
        contrib_auth_views.LogoutView.as_view(
            next_page=reverse_lazy('core-views-index')),
        name='tcms-logout'),
    url(r'^register/$', auth_views.register, name='tcms-register'),
    url(r'^confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$', auth_views.confirm,
        name='tcms-confirm'),

    url(r'^login/$', contrib_auth_views.LoginView.as_view(), name='tcms-login'),
    url(r'^changepassword/$', contrib_auth_views.PasswordChangeView.as_view(),
        name='tcms-password_change'),
    url(r'^changepassword/done/$', contrib_auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'),
    url(r'^passwordreset/$', contrib_auth_views.PasswordResetView.as_view(),
        name='tcms-password_reset'),
    url(r'^passwordreset/done/$', contrib_auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(r'^passwordreset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        contrib_auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^passwordreset/complete/$',
        contrib_auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
