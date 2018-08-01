# -*- coding: utf-8 -*-

from django.urls import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404


def profile(request, username):
    """Show user profiles"""
    user = get_object_or_404(User, username=username)
    return HttpResponseRedirect(reverse('admin:auth_user_change', args=[user.pk]))
