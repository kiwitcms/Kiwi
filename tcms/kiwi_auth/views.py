# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, views
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import RedirectView, View
from django.views.generic.edit import FormView

from tcms.kiwi_auth import forms
from tcms.kiwi_auth.models import UserActivationKey
from tcms.signals import USER_REGISTERED_SIGNAL

User = get_user_model()  # pylint: disable=invalid-name


try:
    from django_tenants.utils import get_public_schema_name
except ImportError:

    def get_public_schema_name():  # pylint: disable=nested-function-found
        return "public"


class LoginViewWithCustomTemplate(
    views.LoginView
):  # pylint: disable=missing-permission-required
    def get_template_names(self):
        return ["registration/custom_login.html", "registration/login.html"]


class PasswordResetView(
    views.PasswordResetView
):  # pylint: disable=missing-permission-required
    form_class = forms.PasswordResetForm


class Register(View):  # pylint: disable=missing-permission-required
    """Register method of account"""

    template_name = "registration/registration_form.html"
    form_class = forms.RegistrationForm
    success_url = reverse_lazy("core-views-index")

    def post(self, request):
        """Post request handler."""
        form = self.form_class(data=request.POST, files=request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        new_user = form.save()
        activation_key = forms.set_activation_key_for(new_user)
        # send a signal that new user has been registered
        USER_REGISTERED_SIGNAL.send(
            sender=form.__class__, request=request, user=new_user
        )

        # Send confirmation email to new user
        if settings.DEFAULT_FROM_EMAIL and settings.AUTO_APPROVE_NEW_USERS:
            forms.send_confirmation_email_to(new_user, request, activation_key)

            msg = _(
                "Your account has been created, please check your mailbox for confirmation"
            )
            messages.add_message(request, messages.SUCCESS, msg)
        else:
            msg = _(
                "Your account has been created, but you need an administrator to activate it"
            )
            messages.add_message(request, messages.WARNING, msg)

            messages.add_message(
                request, messages.INFO, _("Following is the administrator list")
            )
            self.show_messages_with_site_admins_emails_as_links(request)
            self.show_messages_with_super_user_emails_as_links(request)

        return HttpResponseRedirect(self.success_url)

    @staticmethod
    def show_messages_with_site_admins_emails_as_links(request):
        """Show messages with site admins emails as links."""
        for name, email in settings.ADMINS:
            mailto = f'<a href="mailto:{email}">{name}</a>'
            messages.add_message(request, messages.WARNING, mailto)

    @staticmethod
    def show_messages_with_super_user_emails_as_links(request):
        """Show messages with super users emails as links."""
        for user in User.objects.filter(is_superuser=True):
            email_display_name = user.get_full_name() or user.username
            mailto = f'<a href="mailto:{user.email}">{email_display_name}</a>'
            messages.add_message(request, messages.INFO, mailto)

    def get(self, request):
        """Get request handler."""
        return render(request, self.template_name, {"form": self.form_class()})


class Confirm(RedirectView):  # pylint: disable=missing-permission-required
    """Confirm the user registration"""

    http_method_names = ["get"]

    def get_redirect_url(self, *args, **kwargs):
        self.url = self.request.GET.get("next", reverse("core-views-index"))
        activation_key = kwargs["activation_key"]
        try:
            _activation_key = UserActivationKey.objects.select_related("user").get(
                activation_key=activation_key
            )
        except UserActivationKey.DoesNotExist:
            messages.add_message(
                self.request,
                messages.ERROR,
                _("This activation key no longer exists in the database"),
            )
            return super().get_redirect_url(*args, **kwargs)

        if _activation_key.key_expires <= timezone.now():
            messages.add_message(
                self.request, messages.ERROR, _("This activation key has expired")
            )
            return super().get_redirect_url(*args, **kwargs)

        # All thing done, start to active the user and use the user login
        _activation_key.user.is_active = True
        _activation_key.user.save()
        _activation_key.delete()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            _("Your account has been activated successfully"),
        )
        return super().get_redirect_url(*args, **kwargs)


class Profile(View):  # pylint: disable=missing-permission-required
    """Show user profiles"""

    http_method_names = ["get"]

    def get(self, request, pk):  # pylint: disable=no-self-use
        user = get_object_or_404(User, pk=pk)
        return HttpResponseRedirect(reverse("admin:auth_user_change", args=[user.pk]))


@method_decorator(login_required, name="dispatch")
class UsersRouter(View):  # pylint: disable=missing-permission-required
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):  # pylint: disable=no-self-use
        is_multi_tenant = hasattr(request, "tenant")

        if request.user.is_superuser:
            if is_multi_tenant:
                messages.add_message(
                    request,
                    messages.INFO,
                    _("You are viewing records from tenant '%s'") % "MAIN",
                )

            return HttpResponseRedirect("/admin/auth/user/")

        if is_multi_tenant and request.tenant.schema_name != get_public_schema_name():
            messages.add_message(
                request,
                messages.INFO,
                _("You are viewing records from tenant '%s'")
                % request.tenant.schema_name,
            )
            return HttpResponseRedirect("/admin/tcms_tenants/tenant_authorized_users/")

        return HttpResponseRedirect("/admin/auth/user/")


@method_decorator(login_required, name="dispatch")
class GroupsRouter(View):  # pylint: disable=missing-permission-required
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):  # pylint: disable=no-self-use
        is_multi_tenant = hasattr(request, "tenant")
        if request.user.is_superuser:
            if is_multi_tenant:
                messages.add_message(
                    request,
                    messages.INFO,
                    _("You are viewing records from tenant '%s'") % "MAIN",
                )

            return HttpResponseRedirect("/admin/auth/group/")

        if is_multi_tenant and request.tenant.schema_name != get_public_schema_name():
            messages.add_message(
                request,
                messages.INFO,
                _("You are viewing records from tenant '%s'")
                % request.tenant.schema_name,
            )
            return HttpResponseRedirect("/admin/tenant_groups/group/")

        return HttpResponseRedirect("/admin/auth/group/")


@method_decorator(login_required, name="dispatch")
class ResetUserEmail(FormView):  # pylint: disable=missing-permission-required
    template_name = "accounts/reset_user_email.html"
    form_class = forms.ResetUserEmailForm
    target_user = None

    def init_user(self, request, pk):
        self.target_user = request.user

        # admins can reset emails for others
        if request.user.has_perm("auth.change_user"):
            self.target_user = User.objects.get(pk=pk)

    def get(self, request, *args, **kwargs):
        self.init_user(request, kwargs["pk"])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.init_user(request, kwargs["pk"])
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["target_user"] = self.target_user
        return context

    def form_valid(self, form):
        # in case they somehow managed to spoof the form submission
        if (
            self.target_user.pk != self.request.user.pk
            and not self.request.user.has_perm("auth.change_user")
        ):
            raise PermissionDenied

        activation_key = forms.set_activation_key_for(self.target_user)

        self.target_user.email = form.cleaned_data["email_2"]
        self.target_user.is_active = False
        self.target_user.save()

        forms.send_confirmation_email_to(self.target_user, self.request, activation_key)

        msg = _(
            "Email address has been reset, please check inbox for further instructions"
        )
        messages.add_message(self.request, messages.SUCCESS, msg)

        # logout only when modifying myself
        if self.request.user.pk == self.target_user.pk:
            return HttpResponseRedirect(reverse_lazy("tcms-logout"))

        # otherwise maybe they have permissions to view and modify other users
        return HttpResponseRedirect(reverse_lazy("admin-users-router"))
