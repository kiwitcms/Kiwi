# -*- coding: utf-8 -*-

import django_comments as comments
from django.conf import settings
from django.contrib.auth.decorators import permission_required
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


@require_POST
@permission_required("django_comments.can_moderate")
def delete(request):
    """Delete comments via POST request"""
    comments.get_model().objects.filter(
        pk__in=request.POST.getlist('comment_id'),
        site=settings.SITE_ID,
        user=request.user.pk
    ).delete()

    return JsonResponse({'rc': 0, 'response': 'ok'})
