# -*- coding: utf-8 -*-

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from tcms.management.models import (
    Build,
    Classification,
    Component,
    Priority,
    Product,
    Tag,
    Version,
)


class ClassificationAdmin(admin.ModelAdmin):
    search_fields = ("name", "id")
    list_display = ("id", "name")


class ProductsAdmin(admin.ModelAdmin):
    search_fields = ("name", "id")
    list_display = ("id", "name", "classification", "description")
    list_filter = ("id", "name", "classification")


class PriorityAdmin(admin.ModelAdmin):
    search_fields = ("value", "id")
    list_display = ("id", "value", "is_active")
    list_filter = ("is_active",)


class ComponentAdmin(admin.ModelAdmin):
    search_fields = ("name", "id")
    list_display = ("id", "name", "product", "initial_owner", "description")
    list_filter = ("product",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product", "initial_owner")


class VersionAdmin(admin.ModelAdmin):
    search_fields = ("value", "id")
    list_display = ("id", "product", "value")
    list_filter = ("product",)


class BuildAdmin(admin.ModelAdmin):
    search_fields = ("name", "id")
    list_display = ("id", "name", "version", "product_name", "is_active")
    list_filter = ("version__product", "version", "is_active")

    def product_name(self, obj):  # pylint: disable=no-self-use
        return obj.version.product

    product_name.short_description = _("Product")


class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ("file_name", "attachment_id")
    list_display = (
        "attachment_id",
        "file_name",
        "submitter",
        "description",
        "create_date",
        "mime_type",
    )


class TagAdmin(admin.ModelAdmin):
    list_display = ("pk", "name")


admin.site.register(Classification, ClassificationAdmin)
admin.site.register(Product, ProductsAdmin)
admin.site.register(Priority, PriorityAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(Build, BuildAdmin)
admin.site.register(Tag, TagAdmin)
