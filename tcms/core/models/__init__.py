# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.db import models

from tcms.core.models.base import UrlMixin
from tcms.rpc.serializer import Serializer

get_user_model()._meta.ordering = ["username"]


class TCMSActionModel(models.Model, UrlMixin):
    """
    TCMS action models.
    Use for global log system.
    """

    class Meta:
        abstract = True

    @classmethod
    def to_xmlrpc(cls, query=None):
        """
        Convert the query set for XMLRPC
        """
        if query is None:
            query = {}
        serializer = Serializer(queryset=cls.objects.filter(**query))
        return serializer.serialize_queryset()

    def serialize(self):
        """
        Convert the model for XMLPRC
        """
        serializer = Serializer(model=self)
        return serializer.serialize_model()
