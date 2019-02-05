# -*- coding: utf-8 -*-

from datetime import datetime

from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.contrib.auth import views
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from tcms.signals import USER_REGISTERED_SIGNAL
from tcms.kiwi_auth.forms import RegistrationForm
from tcms.kiwi_auth.models import UserActivationKey


User = get_user_model()  # pylint: disable=invalid-name


class LoginViewWithCustomTemplate(views.LoginView):
    def get_template_names(self):
        return ['registration/custom_login.html', 'registration/login.html']


@require_http_methods(['GET', 'POST'])
def register(request):
    """Register method of account"""
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = form.save()
            activation_key = form.set_activation_key()
            # send a signal that new user has been registered
            USER_REGISTERED_SIGNAL.send(sender=form.__class__,
                                        request=request,
                                        user=new_user)

            # Send confirmation email to new user
            if settings.DEFAULT_FROM_EMAIL and settings.AUTO_APPROVE_NEW_USERS:
                form.send_confirm_mail(request, activation_key)

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('Your account has been created, please check your mailbox for confirmation')
                )
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    _('Your account has been created, but you need an administrator to activate it')
                )
                messages.add_message(
                    request,
                    messages.INFO,
                    _('Following is the administrator list')
                )

                # super-users can approve others
                for user in User.objects.filter(is_superuser=True):
                    messages.add_message(
                        request,
                        messages.INFO,
                        '<a href="mailto:{}">{}</a>'.format(user.email,
                                                            user.get_full_name() or user.username)
                    )

                # site admins should be able to do so too
                for name, email in settings.ADMINS:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        '<a href="mailto:{}">{}</a>'.format(email, name)
                    )

            return HttpResponseRedirect(reverse('core-views-index'))
    else:
        form = RegistrationForm()

    context_data = {
        'form': form,
    }
    return render(request, 'registration/registration_form.html', context_data)


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

    if _activation_key.key_expires <= datetime.now():
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
