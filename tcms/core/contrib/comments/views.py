# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.http import require_POST

import django_comments as comments

from .utils import add_comment


@require_POST
def post(request):
    """Post a comment"""

    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()
    _form, _target = add_comment(request, data)

    return JsonResponse({'rc': 0})


@require_POST
@permission_required("comments.can_moderate")
def delete(request):
    """Deletes a comment"""

    ajax_response = {'rc': 0, 'response': 'ok'}
    comments_s = comments.get_model().objects.filter(
        pk__in=request.POST.getlist('comment_id'),
        site__pk=settings.SITE_ID,
        is_removed=False,
        user_id=request.user.id
    )

    if not comments_s:
        if request.is_ajax():
            ajax_response = {'rc': 1, 'response': 'Object does not exist.'}
            return JsonResponse(ajax_response)

        raise ObjectDoesNotExist()

    # Flag the comment as deleted instead of actually deleting it.
    for comment in comments_s:
        if comment.user == request.user:
            flag, created = comments.models.CommentFlag.objects.get_or_create(
                comment=comment,
                user=request.user,
                flag=comments.models.CommentFlag.MODERATOR_DELETION
            )
            comment.is_removed = True
            comment.save()
            comments.signals.comment_was_flagged.send(
                sender=comment.__class__,
                comment=comment,
                flag=flag,
                created=created,
                request=request,
            )

    return JsonResponse(ajax_response)
