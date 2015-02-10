# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete, pre_save

from fields import BlobValueWrapper, BlobField
from base import TCMSContentTypeBaseModel
from base import UrlMixin
from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.core.logs.views import TCMSLog
from tcms.testruns import signals as run_watchers

User._meta.ordering = ['username']


class TCMSActionModel(models.Model, UrlMixin):
    """
    TCMS action models.
    Use for global log system.
    """

    class Meta:
        abstract = True

    @classmethod
    def to_xmlrpc(cls, query={}):
        """
        Convert the query set for XMLRPC
        """
        s = XMLRPCSerializer(queryset=cls.objects.filter(**query))
        return s.serialize_queryset()

    def serialize(self):
        """
        Convert the model for XMLPRC
        """
        s = XMLRPCSerializer(model=self)
        return s.serialize_model()

    def log(self):
        log = TCMSLog(model=self)
        return log.list()

    def log_action(self, who, action):
        log = TCMSLog(model=self)
        log.make(who=who, action=action)

        return log

    def clean(self):
        strip_types = (models.CharField,
                       models.TextField,
                       models.URLField,
                       models.EmailField,
                       models.IPAddressField,
                       models.GenericIPAddressField,
                       models.SlugField)

        for field in self._meta.fields:
            # TODO: hardcode 'notes' here
            if not (field.name is 'notes') and isinstance(field, strip_types):
                value = getattr(self, field.name)
                setattr(self, field.name, value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' '))
