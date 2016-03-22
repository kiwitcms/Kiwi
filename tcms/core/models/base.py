# -*- coding: utf-8 -*-
import urlparse

from django.db import models
from django.conf import settings
from django.contrib.contenttypes import fields
from django.contrib.sites.models import Site

# ----------------------------------------------------------
# UrlMixin is storned from
# http://code.djangoproject.com/wiki/ReplacingGetAbsoluteUrl
# ----------------------------------------------------------


class UrlMixin(object):
    def get_url(self):
        if hasattr(self.get_url_path, 'dont_recurse'):
            raise NotImplemented
        try:
            path = self.get_url_path()
        except NotImplemented:
            raise
        protocol = getattr(settings, "PROTOCOL", "http")
        domain = Site.objects.get_current().domain
        port = getattr(settings, "PORT", "")
        if port:
            assert port.startswith(
                ":"), "The PORT setting must have a preceeding ':'."
        return "%s://%s%s%s" % (protocol, domain, port, path)

    get_url.dont_recurse = True

    def get_url_path(self):
        if hasattr(self.get_url, 'dont_recurse'):
            raise NotImplemented
        try:
            url = self.get_url()
        except NotImplemented:
            raise
        bits = urlparse.urlparse(url)
        return urlparse.urlunparse(('', '') + bits[2:])

    get_url_path.dont_recurse = True


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
        blank=True, null=True)
    object_pk = models.PositiveIntegerField('object ID', blank=True, null=True)
    content_object = fields.GenericForeignKey(ct_field="content_type",
                                               fk_field="object_pk")

    # Metadata about the comment
    site = models.ForeignKey('sites.Site')

    class Meta:
        abstract = True
