# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib import auth
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods

from tcms.core.contrib.auth import get_using_backend
from tcms.core.contrib.auth.forms import RegistrationForm
from tcms.core.contrib.auth.models import UserActivateKey
from tcms.core.views import Prompt


@require_GET
def logout(request):
    """Logout method of account"""
    auth.logout(request)
    return redirect(request.GET.get('next', reverse('core-views-index')))


@require_http_methods(['GET', 'POST'])
def register(request, template_name='registration/registration_form.html'):
    """Register method of account"""

    request_data = request.GET or request.POST

    # Check that registration is allowed by backend
    backend = get_using_backend()
    cr = getattr(backend, 'can_register')  # can register
    if not cr:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Alert,
            info='The backend is not allowed to register.',
            next=request_data.get('next', reverse('core-views-index'))
        ))

    if request.method == 'POST':
        form = RegistrationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            ak = form.set_active_key()

            # Send email to user if mail server is available.
            if form.cleaned_data['email'] and settings.EMAIL_HOST:
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

            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info=msg,
                next=request.POST.get('next', reverse('core-views-index'))
            ))
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
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info=msg,
            next=request.GET.get('next', reverse('core-views-index'))
        ))

    # All thing done, start to active the user and use the user login
    user = ak.user
    user.is_active = True
    user.save(update_fields=['is_active'])
    ak.delete()
    # login(request, user)

    # Response to web browser.
    msg = 'Your account has been activated successfully, click next link to ' \
          're-login.'
    return HttpResponse(Prompt.render(
        request=request,
        info_type=Prompt.Info,
        info=msg,
        next=request.GET.get('next', reverse(
            'tcms-redirect_to_profile'))
    ))
