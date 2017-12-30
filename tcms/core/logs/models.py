# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db import models

from tcms.core.models.base import TCMSContentTypeBaseModel
from .managers import TCMSLogManager


# Create your models here.

class TCMSLogModel(TCMSContentTypeBaseModel):
    who = models.ForeignKey('auth.User', related_name='log_who', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    action = models.TextField()

    objects = TCMSLogManager()

    class Meta:
        abstract = False
        db_table = u'tcms_logs'
        index_together = (('content_type', 'object_pk', 'site'),)

    def __str__(self):
        return self.action

    @classmethod
    def get_logs_for_model(cls, model_class, object_pk):
        ct = ContentType.objects.get_for_model(model_class)
        return cls.objects.filter(content_type=ct, object_pk=object_pk)
