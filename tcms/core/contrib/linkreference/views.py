from http import HTTPStatus

from django import http
from django.forms import IntegerField
from django.forms import ValidationError
from django.contrib.auth.decorators import permission_required
from django.views.decorators.http import require_GET, require_POST

from .models import LinkReference
from .forms import AddLinkReferenceForm

__all__ = ('add', 'remove', 'create_link')


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

        link = LinkReference.objects.create(
            test_case_run_id=target_id,
            name=name,
            url=url)

        return {
            'rc': 0,
            'response': 'ok',
            'data': {
                'pk': link.pk,
                'name': name,
                'url': url,
            }
        }
    return {'rc': 1, 'response': form.errors.as_text()}


@permission_required('testruns.change_testexecution')
@require_POST
def add(request):
    """Add new link to a specific target

    The target should be a valid model within TCMS, which are documented in
    ``LINKREF_TARGET``.

    Incoming request should be a POST request, and contains following
    arguments:

    - target: To which the new link will link to. The available target names
      are documented in the ``LINKREF_TARGET``.
    - target_id: the ID used to construct the concrete target instance, to
      which the new link will be linked.
    - name: a short description to this new link, and accept 64 characters at
      most.
    - url: the actual URL.
    """

    json_data = create_link(request.POST)
    if json_data['rc'] == 0:
        return http.JsonResponse(json_data)
    return http.JsonResponse(json_data, status=HTTPStatus.BAD_REQUEST)


@permission_required('testruns.change_testexecution')
@require_GET
def remove(_request, link_id):
    """ Remove a specific link with ID ``link_id`` """

    field = IntegerField(min_value=1)
    try:
        value = field.clean(link_id)
    except ValidationError as err:
        json_data = {'rc': 1, 'response': '\n'.join(err.messages)}
        return http.JsonResponse(json_data, status=HTTPStatus.BAD_REQUEST)

    # this will silently ignore non-existing objects
    LinkReference.objects.filter(pk=value).delete()

    return http.JsonResponse({
        'rc': 0,
        'response': 'Link has been removed successfully.'
    })
