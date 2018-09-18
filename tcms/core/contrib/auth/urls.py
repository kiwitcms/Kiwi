# -*- coding: utf-8 -*-

from django.conf.urls import url, include
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views

from tcms.core.contrib.auth import views

urlpatterns = [
    url(r'^(?P<username>[\w.@+-]+)/profile/$', views.profile,
        name='tcms-profile'),

    url(r'^register/$', views.register, name='tcms-register'),
    url(r'^confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$', views.confirm,
        name='tcms-confirm'),

    url(r'^login/$', views.LoginViewWithCustomTemplate.as_view(), name='tcms-login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(next_page=reverse_lazy('tcms-login')),
        name='tcms-logout'),

    url('', include('social_django.urls', namespace='social')),

    url(r'^passwordreset/$', auth_views.PasswordResetView.as_view(),
        name='tcms-password_reset'),
    url(r'^passwordreset/done/$', auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(r'^passwordreset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
        auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    url(r'^passwordreset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
