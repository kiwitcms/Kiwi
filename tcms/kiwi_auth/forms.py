# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import override

from tcms.core.utils import request_host_link
from tcms.core.utils.mailto import mailto
from tcms.kiwi_auth.models import UserActivationKey
from tcms.utils.permissions import initiate_user_with_default_setups

User = get_user_model()  # pylint: disable=invalid-name

# actually enable only if app is configured
if "captcha" in settings.INSTALLED_APPS:
    from captcha.fields import ReCaptchaField
else:
    ReCaptchaField = None.__class__  # pylint: disable=invalid-name


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()
    captcha = ReCaptchaField()

    class Meta:
        model = User
        fields = ("username",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(_("A user with that email already exists."))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.is_active = False
        user.set_password(self.cleaned_data["password1"])

        if User.objects.filter(is_superuser=True).count() == 0:
            user.is_superuser = True
            user.is_active = True

        if commit:
            user.save()
            initiate_user_with_default_setups(user)
        return user

    def set_activation_key(self):
        return UserActivationKey.set_random_key_for_user(user=self.instance)

    @override(settings.LANGUAGE_CODE)
    def send_confirm_mail(self, request, activation_key):
        current_site = Site.objects.get(pk=settings.SITE_ID)
        confirm_url = "%s%s" % (
            request_host_link(request, current_site.domain),
            reverse(
                "tcms-confirm",
                args=[
                    activation_key.activation_key,
                ],
            ),
        )
        mailto(
            template_name="email/confirm_registration.txt",
            recipients=self.cleaned_data["email"],
            subject=_("Your new %s account confirmation") % current_site.domain,
            context={
                "user": self.instance,
                "site_domain": current_site.domain,
                "confirm_url": confirm_url,
            },
        )


class PasswordResetForm(
    DjangoPasswordResetForm
):  # pylint: disable=must-inherit-from-model-form
    """
    Overrides the default form b/c it uses Site.objects.get_current()
    which uses an internal cache and produces wrong results when
    kiwitcms-tenants is installed.
    """

    def save(  # pylint: disable=too-many-arguments
        self,
        domain_override=None,
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name=None,
        extra_email_context=None,
    ):
        current_site = Site.objects.get(pk=settings.SITE_ID)
        # call the stock method and just overrides the domain
        super().save(
            current_site.domain,
            subject_template_name,
            email_template_name,
            use_https,
            token_generator,
            from_email,
            request,
            html_email_template_name,
            extra_email_context,
        )
