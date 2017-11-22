# -*- coding: utf-8 -*-
import six

from django.db import models
from django.contrib.contenttypes.models import ContentType

if six.PY3:
    from django.utils.encoding import force_text as force_unicode
else:
    from django.utils.encoding import force_unicode


class TCMSLogManager(models.Manager):
    def for_model(self, model):
        """
        QuerySet for all comments for a particular model (either an instance or
        a class).
        """
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_pk=force_unicode(model._get_pk_val()))
        return qs
