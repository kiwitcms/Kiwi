# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from tcms.core.models.base import UrlMixin


class Classification(models.Model, UrlMixin):
    name = models.CharField(unique=True, max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Product(models.Model, UrlMixin):
    name = models.CharField(unique=True, max_length=255)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

        self.category.get_or_create(name="--default--")
        version, _ = self.version.get_or_create(value="unspecified")
        version.build.get_or_create(name="unspecified")

    class Meta:
        ordering = ["name"]


class Priority(models.Model, UrlMixin):
    value = models.CharField(unique=True, max_length=64)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["value"]
        verbose_name_plural = u"priorities"

    def __str__(self):
        return self.value


class Component(models.Model, UrlMixin):
    name = models.CharField(max_length=64)
    product = models.ForeignKey(
        Product, related_name="component", on_delete=models.CASCADE
    )
    initial_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="initial_owner",
        null=True,
        on_delete=models.CASCADE,
    )
    initial_qa_contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="initial_qa_contact",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    description = models.TextField()

    class Meta:
        ordering = ["name"]
        unique_together = ("product", "name")

    def __str__(self):
        return self.name


class Version(models.Model, UrlMixin):
    value = models.CharField(max_length=192)
    product = models.ForeignKey(
        Product, related_name="version", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ["value"]
        unique_together = ("product", "value")

    def __str__(self):
        return self.value

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        super().save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields,
        )

        self.build.get_or_create(name="unspecified")


class Build(models.Model):
    name = models.CharField(max_length=255)
    version = models.ForeignKey(Version, related_name="build", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = ("version", "name")
        verbose_name = _("Build")
        verbose_name_plural = _("Builds")

    def __str__(self):
        return self.name


class Tag(models.Model, UrlMixin):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]
        verbose_name = u"tag"
        verbose_name_plural = u"tags"

    def __str__(self):
        return self.name

    @classmethod
    def get_or_create(cls, user, tag_name):
        """
        Helper method used to check if @user is allowed
        to automatically create new Tag in the database!

        If they are not, e.g. in environment where users
        are forced to use pre-existing tags created by admin,
        then it will raise a DoesNotExist exception.
        """
        if user.has_perm("management.add_tag"):
            return cls.objects.get_or_create(name=tag_name)

        return cls.objects.get(name=tag_name), False
