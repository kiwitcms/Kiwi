# -*- coding: utf-8 -*-

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.encoding import smart_text
from django.contrib.contenttypes.models import ContentType

from tcms.core.models.base import UrlMixin
from tcms.core.logs.models import TCMSLogModel
from tcms.xmlrpc.serializer import XMLRPCSerializer

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
        serializer = XMLRPCSerializer(queryset=cls.objects.filter(**query))
        return serializer.serialize_queryset()

    def serialize(self):
        """
        Convert the model for XMLPRC
        """
        serializer = XMLRPCSerializer(model=self)
        return serializer.serialize_model()

    def log(self):
        ctype = ContentType.objects.get_for_model(self)
        qs = TCMSLogModel.objects.filter(content_type=ctype,
                                         object_pk=smart_text(self.pk),
                                         site=settings.SITE_ID)
        return qs.select_related('who')

    def log_action(self, who, action):
        TCMSLogModel(content_object=self, who=who, action=action, site_id=settings.SITE_ID).save()

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
                if value:
                    setattr(self, field.name,
                            value.replace('\t', ' ').replace('\n', ' ').replace('\r', ' '))
