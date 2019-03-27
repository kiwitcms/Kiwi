# -*- coding: utf-8 -*-
"""
Functions that help access comments
of objects.
"""
from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site

from django_comments.models import Comment


def add_comment(objs, comments, user, submit_date=None):
    """
    Add django.comment for an object.

    :param objs: List of object to which to add comments
    :type objs: list
    :param comments: The commentary
    :type comments: str
    :param user: Who is adding this
    :type user: A User model
    :param submit_date: A time stamp
    :type submit_date: datetime.datetime

    Example::

        from django.contrib.auth.models import User
        testuser = User.objects.get(email='user@example.com')
        from tcms.testruns.models import TestExecution
        testrun = TestExecution.objects.get(pk=171675)
        comments = 'stupid comments by Homer'
        add_comment([testrun,], comments, testuser)
    """
    site = Site.objects.get(pk=settings.SITE_ID)
    content_type = ContentType.objects.get_for_model(model=objs[0].__class__)
    for obj in objs:
        Comment.objects.create(content_type=content_type,
                               site=site,
                               object_pk=obj.pk,
                               user=user,
                               comment=comments,
                               submit_date=submit_date or datetime.now(),
                               user_email=user.email,
                               user_name=user.username)
