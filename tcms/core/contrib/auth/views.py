# -*- coding: utf-8 -*-

from datetime import datetime

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods

from . import get_using_backend
from .forms import RegistrationForm
from .models import UserActivateKey
from tcms.core.views import Prompt
from tcms.signals import user_registered


@require_http_methods(['GET', 'POST'])
def register(request, template_name='registration/registration_form.html'):
    """Register method of account"""

    request_data = request.GET or request.POST

    # Check that registration is allowed by backend
    backend = get_using_backend()
    cr = getattr(backend, 'can_register')  # can register
    if not cr:
        return Prompt.render(
            request=request,
            info_type=Prompt.Alert,
            info='The backend is not allowed to register.',
            next=request_data.get('next', reverse('core-views-index'))
        )

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

                msg = 'Your account has been created, please check your ' \
                      'mailbox for confirmation.'
            else:
                msg = [
                    '<p>Your account has been created, but you need to contact '
                    'an administrator to active your account.</p>',
                ]
                # If can not send email, prompt to user.
                if settings.ADMINS:
                    msg.append('<p>Following is the admin list</p><ul>')
                    for name, email in settings.ADMINS:
                        msg.append('<li><a href="mailto:{}">{}</a></li>'.format(email, name))
                    msg.append('</ul>')
                msg = ''.join(msg)

            return Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info=msg,
                next=request.POST.get('next', reverse('core-views-index'))
            )
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
        msg = 'This key no longer exist in the database.'
        return Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info=msg,
            next=request.GET.get('next', reverse('core-views-index'))
        )

    if ak.key_expires <= datetime.now():
        msg = 'This key has expired!'
        return Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info=msg,
            next=request.GET.get('next', reverse('core-views-index'))
        )

    # All thing done, start to active the user and use the user login
    user = ak.user
    user.is_active = True
    user.save(update_fields=['is_active'])
    ak.delete()
    # login(request, user)

    # Response to web browser.
    msg = 'Your account has been activated successfully, click next link to ' \
          're-login.'
    return Prompt.render(
        request=request,
        info_type=Prompt.Info,
        info=msg,
        next=request.GET.get('next', reverse(
            'tcms-redirect_to_profile'))
    )
