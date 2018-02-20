# -*- coding: utf-8 -*-

from datetime import datetime

from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods


from . import get_using_backend
from .forms import RegistrationForm
from .models import UserActivateKey
from tcms.signals import user_registered


@require_http_methods(['GET', 'POST'])
def register(request, template_name='registration/registration_form.html'):
    """Register method of account"""
    # Check that registration is allowed by backend
    backend = get_using_backend()
    cr = getattr(backend, 'can_register')  # can register
    if not cr:
        messages.add_message(
            request,
            messages.ERROR,
            _('This backend does not allow user registration')
        )
        return HttpResponseRedirect(reverse('tcms-login'))

    if request.method == 'POST':
        form = RegistrationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = form.save()
            ak = form.set_active_key()
            # send a signal that new user has been registered
            user_registered.send(sender=form.__class__,
                                 request=request,
                                 user=new_user,
                                 backend=backend)

            # Send email to user if email is configured.
            if form.cleaned_data['email'] and settings.DEFAULT_FROM_EMAIL:
                form.send_confirm_mail(request=request, active_key=ak)

                messages.add_message(
                    request,
                    messages.INFO,
                    _('Your account has been created, please check your mailbox for confirmation')
                )
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    _('Your account has been created, but you need an administrator to activate it')
                )
                if settings.ADMINS:
                    messages.add_message(
                        request,
                        messages.INFO,
                        _('Following is the administrator list')
                    )
                    for name, email in settings.ADMINS:
                        messages.add_message(
                            request,
                            messages.INFO,
                            '<a href="mailto:{}">{}</a>'.format(email, name)
                        )

            return HttpResponseRedirect(reverse('core-views-index'))
    else:
        form = RegistrationForm()

    context_data = {
        'form': form,
    }
    return render(request, template_name, context_data)


@require_GET
def confirm(request, activation_key):
    """Confirm the user registration"""

    # Get the object
    try:
        ak = UserActivateKey.objects.select_related('user')
        ak = ak.get(activation_key=activation_key)
    except UserActivateKey.DoesNotExist:
        messages.add_message(
            request,
            messages.ERROR,
            _('This activation key no longer exists in the database')
        )
        return HttpResponseRedirect(request.GET.get('next', reverse('core-views-index')))

    if ak.key_expires <= datetime.now():
        messages.add_message(request, messages.ERROR, _('This activation key has expired'))
        return HttpResponseRedirect(request.GET.get('next', reverse('core-views-index')))

    # All thing done, start to active the user and use the user login
    user = ak.user
    user.is_active = True
    user.save(update_fields=['is_active'])
    ak.delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        _('Your account has been activated successfully')
    )
    return HttpResponseRedirect(request.GET.get('next', reverse('tcms-redirect_to_profile')))
