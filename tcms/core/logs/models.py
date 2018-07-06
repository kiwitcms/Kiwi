# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings

from tcms.core.models.base import TCMSContentTypeBaseModel


class TCMSLogModel(TCMSContentTypeBaseModel):
    who = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='log_who', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    action = models.TextField()

    class Meta:
        abstract = False
        index_together = (('content_type', 'object_pk', 'site'),)

    def __str__(self):
        return self.action
