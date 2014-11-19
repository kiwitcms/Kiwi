# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


def index(request, template_name='index.html'):
    """
    Home page of TCMS
    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))

    return HttpResponseRedirect(
        reverse('tcms.profiles.views.recent', args=[request.user.username])
    )
