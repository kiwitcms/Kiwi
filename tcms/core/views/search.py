# -*- coding: utf-8 -*-

import re

from django.urls import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET
from django.http import Http404

from tcms.testplans.models import TestPlan
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestRun


@require_GET
def search(request):
    """
    Redirect to correct url of the search content
    """

    models = {'plans': TestPlan, 'cases': TestCase, 'runs': TestRun}

    search_content = request.GET.get('search_content')
    search_type = request.GET.get('search_type')

    if not search_content or not search_type:
        raise Http404

    if search_type not in models:
        raise Http404

    try_to_get_object = re.match('^\d+$', search_content) is not None
    model = models[search_type]

    if try_to_get_object:
        pk = int(search_content)
        objects = model.objects.filter(pk=pk).only('pk')
        if objects:
            return HttpResponseRedirect(
                reverse('{}-get'.format(model._meta.app_label), args=[pk]))

    url = '{}?a=search&search={}'.format(
        reverse('{}-all'.format(model._meta.app_label)), search_content)
    return HttpResponseRedirect(url)
