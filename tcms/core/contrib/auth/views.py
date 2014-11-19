# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext

from tcms.core.views import Prompt
from models import UserActivateKey


def logout(request):
    """
    Login method of account
    """
    from django.contrib.auth import logout

    logout(request)
    return redirect(
        request.REQUEST.get('next', reverse('tcms.core.views.index')))


def register(request, template_name='registration/registration_form.html'):
    """
    Register method of account
    """
    from tcms.core.contrib.auth import get_using_backend
    from forms import RegistrationForm

    # Check the register is allowed by backend
    backend = get_using_backend()
    cr = getattr(backend, 'can_register')  # can register
    if not cr:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Alert,
            info='The backend is not allow to register.',
            next=request.REQUEST.get('next', reverse('tcms.core.views.index'))
        ))

    if request.method == 'POST':
        form = form = RegistrationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            ak = form.set_active_key()

            # Send email to user if mail server availabel.
            if form.cleaned_data['email'] and settings.EMAIL_HOST:
                form.send_confirm_mail(request=request, active_key=ak)

                msg = 'Your accounts has been create, please check your ' \
                      'mailbox for active.'
                return HttpResponse(Prompt.render(
                    request=request,
                    info_type=Prompt.Info,
                    info=msg,
                    next=request.REQUEST.get('next',
                                             reverse('tcms.core.views.index'))
                ))

            # If can not send email, prompt to user.
            msg = 'Your accounts has been create, but you need to contact ' \
                  'admins to active your account.'
            if settings.ADMINS:
                msg += '<p>Following is the admin list</p><ul>'
                for admin in settings.ADMINS:
                    msg += '<li><a href="mailto:%s">%s</a></li>' % (
                        admin[1], admin[0])
                msg += '</ul>'

            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info=msg,
                next=request.REQUEST.get('next',
                                         reverse('tcms.core.views.index'))
            ))
    else:
        form = RegistrationForm()

    context_data = {
        'form': form,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def confirm(request, activation_key):
    """
    Confirm the user registeration
    """

    # Get the object
    try:
        ak = UserActivateKey.objects.select_related('user')
        ak = ak.get(activation_key=activation_key)
    except UserActivateKey.DoesNotExist:
        msg = 'They key is no longer exist in database.'
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info=msg,
            next=request.REQUEST.get('next', reverse('tcms.core.views.index'))
        ))

    # All thing done, start to active the user and use the user login
    user = ak.user
    user.is_active = True
    user.save()
    ak.delete()
    # login(request, user)

    # Response to web browser.
    msg = 'Your accound has been activate successful, click next link to ' \
          're-login.'
    return HttpResponse(Prompt.render(
        request=request,
        info_type=Prompt.Info,
        info=msg,
        next=request.REQUEST.get('next', reverse(
            'tcms.profiles.views.redirect_to_profile'))
    ))
