# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from tcms.profiles.models import UserProfile
from tcms.profiles.forms import UserProfileForm


@require_http_methods(['GET', 'POST'])
@login_required
@csrf_protect
def profile(request, username):
    """Edit the profiles of the user"""
    user = get_object_or_404(User, username=username)

    try:
        user_profile = UserProfile.get_user_profile(user)
    except ObjectDoesNotExist:
        user_profile = UserProfile.objects.create(user=user)
    form = UserProfileForm(instance=user_profile)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('Information successfully updated'))
    context_data = {
        'user_profile': user_profile,
        'form': form,
    }
    return render(request, 'profile/info.html', context_data)
