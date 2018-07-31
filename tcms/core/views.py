# -*- coding: utf-8 -*-
from django import http
from django.urls import reverse
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token


def index(request):
    """
    Home page of TCMS
    """
    return http.HttpResponseRedirect(reverse('tcms-dashboard'))


def navigation(request):
    """
    iframe navigation workaround until we migrate everything to patternfly
    """
    return render(request, 'navigation.html')


@requires_csrf_token
def server_error(request):
    """
        Render the error page with request object which supports
        static URLs so we can load a nice picture.
    """
    template = loader.get_template('500.html')
    return http.HttpResponseServerError(template.render({}, request))
