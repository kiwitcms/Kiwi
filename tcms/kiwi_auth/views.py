# -*- coding: utf-8 -*-
# pylint: disable=missing-permission-required

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, views
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic.base import View

from tcms.kiwi_auth import forms
from tcms.kiwi_auth.models import UserActivationKey
from tcms.signals import USER_REGISTERED_SIGNAL
from tcms.kiwi_auth.forms import RegistrationForm

User = get_user_model()  # pylint: disable=invalid-name


class LoginViewWithCustomTemplate(views.LoginView):
    def get_template_names(self):
        return ['registration/custom_login.html', 'registration/login.html']


class PasswordResetView(views.PasswordResetView):
    form_class = forms.PasswordResetForm


class Register(View):
    """Register method of account"""
    template_name = 'registration/registration_form.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('core-views-index')

    def post(self, request):
        """ Post request handler. """
        form = self.form_class(data=request.POST, files=request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        new_user = form.save()
        activation_key = form.set_activation_key()
        # send a signal that new user has been registered
        USER_REGISTERED_SIGNAL.send(sender=form.__class__, request=request, user=new_user)

        # Send confirmation email to new user
        if settings.DEFAULT_FROM_EMAIL and settings.AUTO_APPROVE_NEW_USERS:
            form.send_confirm_mail(request, activation_key)

            msg = _('Your account has been created, please check your mailbox for confirmation')
            messages.add_message(request, messages.SUCCESS, msg)
        else:
            msg = _('Your account has been created, but you need an administrator to activate it')
            messages.add_message(request, messages.WARNING, msg)

            messages.add_message(request, messages.INFO, _('Following is the administrator list'))
            self.show_messages_with_site_admins_emails_as_links(request)
            self.show_messages_with_super_user_emails_as_links(request)

        return HttpResponseRedirect(self.success_url)

    @staticmethod
    def show_messages_with_site_admins_emails_as_links(request):
        """ Show messages with site admins emails as links. """
        for name, email in settings.ADMINS:
            mailto = '<a href="mailto:{}">{}</a>'.format(email, name)
            messages.add_message(request, messages.WARNING, mailto)

    @staticmethod
    def show_messages_with_super_user_emails_as_links(request):
        """ Show messages with super users emails as links. """
        for user in User.objects.filter(is_superuser=True):
            email_display_name = user.get_full_name() or user.username
            mailto = '<a href="mailto:{}">{}</a>'.format(user.email, email_display_name)
            messages.add_message(request, messages.INFO, mailto)

    def get(self, request):
        """ Get request handler. """
        return render(request, self.template_name, {'form': self.form_class()})


@require_GET
def confirm(request, activation_key):
    """Confirm the user registration"""

    # Get the object
    try:
        _activation_key = UserActivationKey.objects.select_related('user')
        _activation_key = _activation_key.get(activation_key=activation_key)
    except UserActivationKey.DoesNotExist:
        messages.add_message(
            request,
            messages.ERROR,
            _('This activation key no longer exists in the database')
        )
        return HttpResponseRedirect(request.GET.get('next', reverse('core-views-index')))

    if _activation_key.key_expires <= timezone.now():
        messages.add_message(request, messages.ERROR, _('This activation key has expired'))
        return HttpResponseRedirect(request.GET.get('next', reverse('core-views-index')))

    # All thing done, start to active the user and use the user login
    user = _activation_key.user
    user.is_active = True
    user.save(update_fields=['is_active'])
    _activation_key.delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        _('Your account has been activated successfully')
    )
    return HttpResponseRedirect(request.GET.get('next', reverse('core-views-index')))


def profile(request, username):
    """Show user profiles"""
    user = get_object_or_404(User, username=username)
    return HttpResponseRedirect(reverse('admin:auth_user_change', args=[user.pk]))
