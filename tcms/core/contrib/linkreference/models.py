# -*- coding: utf-8 -*-

from django.db import models

__all__ = ('LinkReference', )


class LinkReference(models.Model):
    object_pk = models.PositiveIntegerField('object ID', blank=True, null=True, db_index=True)

    name = models.CharField(max_length=64, blank=True, default='')
    url = models.URLField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tcms_linkrefs'
