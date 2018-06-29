# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.conf import settings

from tcms.core.models.base import TCMSContentTypeBaseModel
from .managers import TCMSLogManager


# Create your models here.

class TCMSLogModel(TCMSContentTypeBaseModel):
    who = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='log_who', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    action = models.TextField()

    objects = TCMSLogManager()

    class Meta:
        abstract = False
        index_together = (('content_type', 'object_pk', 'site'),)

    def __str__(self):
        return self.action

    @classmethod
    def get_logs_for_model(cls, model_class, object_pk):
        content_type = ContentType.objects.get_for_model(model_class)
        return cls.objects.filter(content_type=content_type, object_pk=object_pk)
