# -*- coding: utf-8 -*-
'''
Functions that help access comments
of objects.
'''

# from django
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django_comments.models import Comment

# from stdlib
from datetime import datetime

_SITE = Site.objects.get(pk=settings.SITE_ID)


def add_comment(objs, comments, user, submit_date=None):
    '''
    Generic approach adding django.comment for an object.
    params:
        @objs: [model, model,]
        @submit_date: datetime object
    >>> from django.contrib.auth.models import User
    >>> testuser = User.objects.get(email='user@example.com')
    >>> from tcms.testruns.models import TestCaseRun as Run
    >>> testrun = Run.objects.get(pk=171675)
    >>> comments = 'stupid comments by Homer'
    >>> add_comment([testrun,], comments, testuser)
    '''
    c_type = ContentType.objects.get_for_model(model=objs[0].__class__)
    create_comment = Comment.objects.create
    for obj in objs:
        create_comment(content_type=c_type,
                       site=_SITE,
                       object_pk=obj.pk,
                       user=user,
                       comment=comments,
                       submit_date=submit_date or datetime.now(),
                       user_email=user.email,
                       user_name=user.username)


if __name__ == '__main__':
    import doctest

    doctest.testmod()
