# -*- coding: utf-8 -*-

from django.db import models


class LinkReference(models.Model):
    execution = models.ForeignKey("testruns.TestExecution", on_delete=models.CASCADE)

    name = models.CharField(max_length=64, blank=True, default="")
    url = models.URLField(db_index=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    is_defect = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.name
