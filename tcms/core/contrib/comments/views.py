# -*- coding: utf-8 -*-

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .utils import add_comment


@require_POST
def post(request):
    """Post a comment"""

    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()
    _form, _target = add_comment(request, data)

    return JsonResponse({'rc': 0})
