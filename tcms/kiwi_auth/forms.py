# -*- coding: utf-8 -*-
from django import forms
from django.urls import reverse
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

from tcms.core.utils import request_host_link
from tcms.core.utils.mailto import mailto
from tcms.kiwi_auth.models import UserActivationKey
from tcms.utils.permissions import initiate_user_with_default_setups


User = get_user_model()  # pylint: disable=invalid-name


class RegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ("username",)

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError(
            _("A user with that email already exists."))

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False
        user.set_password(self.cleaned_data["password1"])

        if User.objects.filter(is_superuser=True).count() == 0:
            user.is_superuser = True

        if commit:
            user.save()
            initiate_user_with_default_setups(user)
        return user

    def set_activation_key(self):
        return UserActivationKey.set_random_key_for_user(user=self.instance)

    def send_confirm_mail(self, request, activation_key):
        current_site = Site.objects.get_current()
        confirm_url = '%s%s' % (
            request_host_link(request, current_site.domain),
            reverse('tcms-confirm',
                    args=[activation_key.activation_key, ])
        )
        mailto(
            template_name='email/confirm_registration.txt', recipients=self.cleaned_data['email'],
            subject=_('Your new %s account confirmation') % current_site.domain,
            context={
                'user': self.instance,
                'site_domain': current_site.domain,
                'confirm_url': confirm_url,
            }
        )
