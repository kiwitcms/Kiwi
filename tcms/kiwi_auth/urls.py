# -*- coding: utf-8 -*-

from django.conf.urls import url
from django.urls import reverse_lazy
from django.contrib.auth import views as contrib_auth_views

from tcms.kiwi_auth import views

urlpatterns = [
    url(r'^(?P<username>[\w.@+-]+)/profile/$', views.profile,
        name='tcms-profile'),

    url(r'^register/$', views.register, name='tcms-register'),
    url(r'^confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$', views.confirm,
        name='tcms-confirm'),

    url(r'^login/$', views.LoginViewWithCustomTemplate.as_view(), name='tcms-login'),
    url(r'^logout/$',
        contrib_auth_views.LogoutView.as_view(next_page=reverse_lazy('tcms-login')),
        name='tcms-logout'),


    url(r'^passwordreset/$', contrib_auth_views.PasswordResetView.as_view(),
        name='tcms-password_reset'),
    url(r'^passwordreset/done/$', contrib_auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(r'^passwordreset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        contrib_auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^passwordreset/complete/$',
        contrib_auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
