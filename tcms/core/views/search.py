# -*- coding: utf-8 -*-

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_GET


@require_GET
def search(request):
    """
    Redirect to correct url of the search content
    """

    request_content = request.GET.get('search_content', '')
    request_type = request.GET.get('search_type')

    # Get search contents
    search_types = {
        'plans': (
            'testplans', 'testplan', reverse('tcms.testplans.views.all')),
        'runs': (
            'testruns', 'testrun', reverse('tcms.testruns.views.all')),
        'cases': (
            'testcases', 'testcase', reverse('tcms.testcases.views.all'))
    }

    search_type = search_types.get(request_type)

    app_label = search_type[0]
    model = search_type[1]
    base_search_url = search_type[2]

    # Try to get the object directly
    try:
        request_content = int(request_content)
        target = models.get_model(*[app_label, model])._default_manager.get(
            pk=request_content)
        url = '%s' % (
            reverse('tcms.%s.views.get' % app_label, args=[target.pk]),
        )

        return HttpResponseRedirect(url)
    except ObjectDoesNotExist:
        pass
    except ValueError:
        pass

    # Redirect to search all page
    url = '%s?a=search&search=%s' % (base_search_url, request_content)

    return HttpResponseRedirect(url)
