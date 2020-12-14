# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.conf import settings
from django.db import models
from django.urls import reverse

from tcms.core.models.base import UrlMixin


class Bug(models.Model, UrlMixin):
    summary = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # True means bug is still open
    status = models.BooleanField(default=True, db_index=True)

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="repoted_bugs"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assigned_bugs",
        null=True,
        blank=True,
    )

    product = models.ForeignKey("management.Product", on_delete=models.CASCADE)
    version = models.ForeignKey("management.Version", on_delete=models.CASCADE)
    build = models.ForeignKey("management.Build", on_delete=models.CASCADE)

    executions = models.ManyToManyField("testruns.TestExecution", related_name="bugs")
    tags = models.ManyToManyField("management.Tag", related_name="bugs")

    def __str__(self):
        return "BUG-%d: %s " % (self.pk, self.summary)

    def _get_absolute_url(self):
        return reverse(
            "bugs-get",
            args=[
                self.pk,
            ],
        )

    def get_absolute_url(self):
        return self._get_absolute_url()
