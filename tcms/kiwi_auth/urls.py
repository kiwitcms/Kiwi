# -*- coding: utf-8 -*-

from django.contrib.auth import views as contrib_auth_views
from django.urls import re_path, reverse_lazy

from tcms.kiwi_auth import views

urlpatterns = [
    re_path(
        r"^(?P<username>[\w.@+-]+)/profile/$",
        views.Profile.as_view(),
        name="tcms-profile",
    ),
    re_path(r"^register/$", views.Register.as_view(), name="tcms-register"),
    re_path(
        r"^confirm/(?P<activation_key>[A-Za-z0-9\-]+)/$",
        views.Confirm.as_view(),
        name="tcms-confirm",
    ),
    re_path(
        r"^login/$", views.LoginViewWithCustomTemplate.as_view(), name="tcms-login"
    ),
    re_path(
        r"^logout/$",
        contrib_auth_views.LogoutView.as_view(next_page=reverse_lazy("tcms-login")),
        name="tcms-logout",
    ),
    re_path(
        r"^passwordreset/$",
        views.PasswordResetView.as_view(),
        name="tcms-password_reset",
    ),
    re_path(
        r"^passwordreset/done/$",
        contrib_auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    re_path(
        r"^passwordreset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$",
        contrib_auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    re_path(
        r"^passwordreset/complete/$",
        contrib_auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
