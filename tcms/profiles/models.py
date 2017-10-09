# -*- coding: utf-8 -*-
from django.db import models

from tcms.core.models import TCMSContentTypeBaseModel


class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', unique=True, related_name='profile', on_delete=models.CASCADE)
    phone_number = models.CharField(blank=True, default='', max_length=128)
    url = models.URLField(blank=True, default='')
    im = models.CharField(blank=True, default='', max_length=128)
    im_type_id = models.IntegerField(blank=True, default=1, null=True)
    address = models.TextField(blank=True, default='')
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = u'tcms_user_profiles'

    def get_im(self):
        from forms import IM_CHOICES

        if not self.im:
            return None

        for c in IM_CHOICES:
            if self.im_type_id == c[0]:
                return '[%s] %s' % (c[1], self.im)

    @classmethod
    def get_user_profile(cls, user):
        return cls.objects.get(user=user)

#
# TCMS Bookmarks in profile models
#


class BookmarkCategory(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=1024)

    class Meta:
        db_table = u'tcms_bookmark_categories'

    def __str__(self):
        return self.name


class Bookmark(TCMSContentTypeBaseModel):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    category = models.ForeignKey(BookmarkCategory, blank=True, null=True,
                                 related_name='bookmark', on_delete=models.CASCADE)
    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True, null=True)
    url = models.CharField(max_length=8192)

    class Meta:
        db_table = u'tcms_bookmarks'
        index_together = (('content_type', 'object_pk', 'site'),)

    def __str__(self):
        return self.name
