# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render


def index(request):
    """
    Home page of TCMS
    """

    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('tcms-login'))

    return HttpResponseRedirect(
        reverse('tcms-recent', args=[request.user.username])
    )


def navigation(request):
    """
    iframe navigation workaround until we migrate everything to patternfly
    """
    return render(request, 'navigation.html')
