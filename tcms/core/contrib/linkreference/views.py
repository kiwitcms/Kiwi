# -*- coding: utf-8 -*-

import json

from django.forms import IntegerField
from django.forms import ValidationError
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_GET, require_POST

from .models import LinkReference
from .forms import AddLinkReferenceForm, BasicValidationForm
from tcms.core.responses import HttpJSONResponse
from tcms.core.responses import HttpJSONResponseBadRequest
from tcms.core.responses import HttpJSONResponseServerError

__all__ = ('add', 'get', 'remove', 'create_link')


def create_link(data):
    """
    .. function:: create_link(data)

        Create a link reference to an object. ``data`` is a dict with the
        following keys:

        :param name: name of the reference
        :type name: str
        :param url: URL
        :type url: str
        :param target_id: PK of the object we link to
        :type target_id: int
        :return: Data suitable for JSON response to clients
        :rtype: dict
    """
    form = AddLinkReferenceForm(data)
    if form.is_valid():
        name = form.cleaned_data['name']
        url = form.cleaned_data['url']
        target_id = form.cleaned_data['target_id']

        LinkReference.objects.create(
            object_pk=target_id,
            name=name,
            url=url)

        return {
            'rc': 0,
            'response': 'ok',
            'data': {'name': name, 'url': url}
        }
    else:
        return {'rc': 1, 'response': form.errors.as_text()}


@permission_required('testruns.change_testcaserun')
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

    jd = create_link(request.POST)
    if jd['rc'] == 0:
        return HttpJSONResponse(content=json.dumps(jd))
    else:
        return HttpJSONResponseBadRequest(content=json.dumps(jd))


@require_GET
def get(request):
    '''Get links of specific instance of content type

    - target: The model name of the instance being searched
    - target_id: The ID of the instance

    Only accept GET request from client.
    '''

    form = BasicValidationForm(request.GET)

    if form.is_valid():
        target_id = form.clean_data['target_id']

        try:
            links = LinkReference.objects.filter(object_pk=target_id)
        except Exception as err:
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


@permission_required('testruns.change_testcaserun')
@require_GET
def remove(request, link_id):
    ''' Remove a specific link with ID ``link_id`` '''

    field = IntegerField(min_value=1)
    try:
        value = field.clean(link_id)
    except ValidationError as err:
        jd = json.dumps({'rc': 1, 'response': '\n'.join(err.messages)})
        return HttpJSONResponseBadRequest(content=jd)

    # this will silently ignore non-existing objects
    LinkReference.objects.filter(pk=value).delete()

    return HttpJSONResponse(
        content=json.dumps(
            {'rc': 0,
             'response': 'Link has been removed successfully.'}))
