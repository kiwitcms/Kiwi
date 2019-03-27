# -*- coding: utf-8 -*-

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

import django_comments


# todo: this is duplicate with tcms.core.helpers.comments.utils
# and is only used in tests and core/ajax.py. Should be removed
# in favor of the other method!
def add_comment(request, data):
    """
        Helper method which is used to add comments to objects.

        :returns: Tuple of (form, target) where form is the comments form object
                  and target is the object we're trying to comment about.
        :rtype: tuple
    """
    if request.user.is_authenticated:
        if not data.get('name'):
            data["name"] = request.user.get_full_name() or request.user.username
        if not data.get('email'):
            data["email"] = request.user.email

    # Look up the object we're trying to comment about
    ctype = data.get("content_type")
    object_pk = data.get("object_pk")

    model = apps.get_model(*ctype.split(".", 1))
    target = model.objects.get(pk=object_pk)

    # Construct the comment form
    form = django_comments.get_form()(target, data=data)
    if not form.is_valid():
        return form, target

    # Otherwise create the comment
    comment = form.get_comment_object()
    comment.ip_address = request.META.get("REMOTE_ADDR", None)
    if request.user.is_authenticated:
        comment.user = request.user

    # Signal that the comment is about to be saved
    django_comments.signals.comment_will_be_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )

    # Save the comment and signal that it was saved
    comment.is_removed = False
    comment.save()
    django_comments.signals.comment_was_posted.send(
        sender=comment.__class__,
        comment=comment,
        request=request
    )

    return form, target


def get_comments(obj):
    """Get comments for obj"""

    content_type = ContentType.objects.get_for_model(obj)
    comments = django_comments.models.Comment.objects.filter(content_type=content_type,
                                                             object_pk=obj.pk,
                                                             site=settings.SITE_ID,
                                                             is_removed=False)
    comments = comments.select_related('user').only('submit_date', 'user__username', 'comment')
    comments.order_by('pk')
    return comments
