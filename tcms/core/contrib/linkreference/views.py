# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_GET, require_POST
import json

from forms import AddLinkReferenceForm, BasicValidationForm
from models import create_link, LinkReference
from tcms.core.responses import HttpJSONResponse
from tcms.core.responses import HttpJSONResponseBadRequest
from tcms.core.responses import HttpJSONResponseServerError

__all__ = ('add', 'get', 'remove', )


@user_passes_test(lambda u: u.has_perm('testruns.change_testcaserun'))
@require_POST
def add(request):
    '''Add new link to a specific target

    The target should be a valid model within TCMS, which are documented in
    ``LINKREF_TARGET``.

    Incoming request should be a POST request, and contains following
    arguments:

    - target: To which the new link will link to. The avialable target names
      are documented in the ``LINKREF_TARGET``.
    - target_id: the ID used to construct the concrete target instance, to
      which the new link will be linked.
    - name: a short description to this new link, and accept 64 characters at
      most.
    - url: the actual URL.
    '''

    form = AddLinkReferenceForm(request.POST)
    if form.is_valid():
        name = form.cleaned_data['name']
        url = form.cleaned_data['url']
        target_id = form.cleaned_data['target_id']
        model_class = form.cleaned_data['target']

        model_instance = model_class.objects.get(pk=target_id)
        create_link(name=name, url=url, link_to=model_instance)

        jd = json.dumps(
            {'rc': 0, 'response': 'ok',
             'data': {'name': name, 'url': url}})
        return HttpJSONResponse(content=jd)

    else:
        jd = json.dumps(
            {'rc': 1, 'response': form.errors.as_text()})
        return HttpJSONResponseBadRequest(content=jd)


@require_GET
def get(request):
    '''Get links of specific instance of content type

    - target: The model name of the instance being searched
    - target_id: The ID of the instance

    Only accept GET request from client.
    '''

    form = BasicValidationForm(request.GET)

    if form.is_valid():
        model_class = form.clean_data['target']
        target_id = form.clean_data['target_id']

        try:
            model_instance = model_class.objects.get(pk=target_id)
            links = LinkReference.get_from(model_instance)
        except Exception, err:
            jd = json.dumps({'rc': 1, 'response': str(err)})
            return HttpJSONResponseServerError(content=jd)

        jd = []
        for link in links:
            jd.append({'name': link.name, 'url': link.url})
        jd = json.dumps(jd)

        return HttpJSONResponse(content=jd)

    else:
        jd = json.dumps(
            {'rc': 1, 'response': form.errors.as_text()})
        return HttpJSONResponseBadRequest(content=jd)


@user_passes_test(lambda u: u.has_perm('testruns.change_testcaserun'))
@require_GET
def remove(request, link_id):
    ''' Remove a specific link with ID ``link_id`` '''

    from django.forms import IntegerField
    from django.forms import ValidationError

    field = IntegerField(min_value=1)
    try:
        value = field.clean(link_id)
    except ValidationError, err:
        jd = json.dumps({'rc': 1, 'response': '\n'.join(err.messages)})
        return HttpJSONResponseBadRequest(content=jd)

    try:
        LinkReference.unlink(value)
    except Exception, err:
        jd = json.dumps({'rc': 1, 'response': str(err)})
        return HttpJSONResponseBadRequest(content=jd)

    return HttpJSONResponse(
        content=json.dumps(
            {'rc': 0,
             'response': 'Link has been removed successfully.'}))
