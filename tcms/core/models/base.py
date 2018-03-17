# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.sites.models import Site

from tcms.core.utils import request_host_link


class UrlMixin(object):
    """Mixin class for getting full URL"""

    def get_full_url(self):
        site = Site.objects.get_current()
        host_link = request_host_link(None, site.domain)
        return '{}/{}'.format(host_link, self.get_absolute_url().strip('/'))


class TCMSContentTypeBaseModel(models.Model):
    """
    TCMS log models.
    The code is from comments contrib from Django
    """

    # Content-object field
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        verbose_name='content type',
        related_name="content_type_set_for_%(class)s",
        blank=True, null=True, on_delete=models.CASCADE)
    object_pk = models.PositiveIntegerField('object ID', blank=True, null=True)
    content_object = GenericForeignKey(ct_field="content_type", fk_field="object_pk")

    # Metadata about the comment
    site = models.ForeignKey('sites.Site', on_delete=models.CASCADE)

    class Meta:
        abstract = True
