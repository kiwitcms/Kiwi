# -*- coding: utf-8 -*-
from django.db import models
from django.http import HttpResponse
import json
from django.shortcuts import render_to_response
from django.template import RequestContext
import django_comments
from django_comments import signals
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import permission_required


def all(request, template_name='comments/comments.html'):
    """
    List the comment of a specific object
    """
    # Fill out some initial data fields from an authenticated user, if present
    data = request.REQUEST.copy()

    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")

    try:
        model = models.get_model(*ctype.split(".", 1))
        target = model._default_manager.get(pk=object_pk)
    except:
        raise

    context_data = {
        'object': target,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def post(request, template_name='comments/comments.html'):
    """
    Post a comment.
    HTTP POST is required.
    """
    # Fill out some initial data fields from an authenticated user, if present
    data = request.POST.copy()

    if request.user.is_authenticated():
        if not data.get('name', ''):
            data["name"] = \
                request.user.get_full_name() or request.user.username
        if not data.get('email', ''):
            data["email"] = request.user.email

    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")

    try:
        model = models.get_model(*ctype.split(".", 1))
        target = model._default_manager.get(pk=object_pk)
    except:
        raise

    # Construct the comment form
    form = django_comments.get_form()(target, data=data)
    if not form.is_valid():
        context_data = {
            'object': target,
            'form': form,
        }
        return render_to_response(template_name, context_data,
                                  context_instance=RequestContext(request))

    # Otherwise create the comment
    comment = form.get_comment_object()
    comment.ip_address = request.META.get("REMOTE_ADDR", None)
    if request.user.is_authenticated():
        comment.user = request.user

    # Signal that the comment is about to be saved
    signals.comment_will_be_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )

    # Save the comment and signal that it was saved
    comment.is_removed = False
    comment.save()
    signals.comment_was_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )

    context_data = {
        'object': target,
        'form': form,
    }
    return render_to_response(template_name, context_data,
                              context_instance=RequestContext(request))


def delete(request, next=None):
    """
    Deletes a comment. Confirmation on GET, action on POST. Requires the "can
    moderate comments" permission.
    """
    from django.conf import settings

    ajax_response = {'rc': 0, 'response': 'ok'}
    comments_s = django_comments.get_model().objects.filter(
        pk__in=request.REQUEST.getlist('comment_id'),
        site__pk=settings.SITE_ID,
        is_removed=False,
        user_id=request.user.id
    )

    if not comments_s:
        if request.is_ajax():
            ajax_response = {'rc': 1, 'response': 'Object does not exist.'}
            return HttpResponse(json.dumps(ajax_response))

        raise ObjectDoesNotExist()

    # Delete on POST
    # Flag the comment as deleted instead of actually deleting it.
    for comment in comments_s:
        if comment.user == request.user:
            flag, created = django_comments.models.CommentFlag.objects.get_or_create(
                comment=comment,
                user=request.user,
                flag=django_comments.models.CommentFlag.MODERATOR_DELETION
            )
            comment.is_removed = True
            comment.save()
            signals.comment_was_flagged.send(
                sender=comment.__class__,
                comment=comment,
                flag=flag,
                created=created,
                request=request,
            )

    return HttpResponse(json.dumps(ajax_response))


delete = permission_required("django_comments.can_moderate")(delete)
