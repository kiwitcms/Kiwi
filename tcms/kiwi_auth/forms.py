# -*- coding: utf-8 -*-
from captcha import fields
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
from tcms.core.utils.mailto import custom_email_validators, mailto
from tcms.kiwi_auth.models import UserActivationKey
from tcms.utils.permissions import initiate_user_with_default_setups

User = get_user_model()  # pylint: disable=invalid-name


class CustomCaptchaTextInput(fields.CaptchaTextInput):
    template_name = "captcha_field.html"


def validate_email_already_in_use(email):
    if User.objects.filter(email__iexact=email.strip()).exists():
        raise forms.ValidationError(_("A user with that email already exists."))


def set_activation_key_for(user):
    return UserActivationKey.set_random_key_for_user(user=user)


@override(settings.LANGUAGE_CODE)
def send_confirmation_email_to(user, request, activation_key):
    current_site = Site.objects.get(pk=settings.SITE_ID)
    confirm_url = request_host_link(request, current_site.domain) + reverse(
        "tcms-confirm",
        args=[
            activation_key.activation_key,
        ],
    )

    mailto(
        template_name="email/confirm_registration.txt",
        recipients=[user.email],
        subject=_("Please confirm your Kiwi TCMS account email address"),
        context={
            "user": user,
            "confirm_url": confirm_url,
        },
    )


class RegistrationForm(UserCreationForm):  # pylint: disable=too-many-ancestors
    email = forms.EmailField(
        validators=[validate_email_already_in_use, custom_email_validators],
    )
    captcha = (
        fields.CaptchaField(
            widget=CustomCaptchaTextInput(attrs={"class": "form-control"})
        )
        if settings.USE_CAPTCHA
        else None
    )

    class Meta:
        model = User
        fields = ("username",)

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


class PasswordResetForm(
    DjangoPasswordResetForm
):  # pylint: disable=must-inherit-from-model-form
    """
    Overrides the default form b/c it uses Site.objects.get_current()
    which uses an internal cache and produces wrong results when
    kiwitcms-tenants is installed.
    """

    captcha = (
        fields.CaptchaField(
            widget=CustomCaptchaTextInput(attrs={"class": "form-control"})
        )
        if settings.USE_CAPTCHA
        else None
    )

    def save(  # pylint: disable=too-many-arguments,too-many-positional-arguments
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


class ResetUserEmailForm(forms.Form):  # pylint: disable=must-inherit-from-model-form
    email_1 = forms.EmailField(
        validators=[validate_email_already_in_use, custom_email_validators],
    )
    email_2 = forms.EmailField()

    def clean_email_2(self):
        email_01 = self.cleaned_data.get("email_1")
        email_02 = self.cleaned_data.get("email_2")
        if email_01 and email_02 and email_01 != email_02:
            raise forms.ValidationError(_("Email mismatch"))
        return email_02
