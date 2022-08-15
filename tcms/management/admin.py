# -*- coding: utf-8 -*-

from django import forms
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


class BuildAdminForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = "__all__"

    class Media:
        js = [
            "js/jsonrpc.js",
            "js/utils.js",
            "management/js/build_admin.js",
        ]

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label="---------",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # POST request for add|change view
        if args:
            post = args[0]
            self.populate(post.get("product", -1))
        # GET request for change view
        elif self.instance.pk:
            self.fields["product"].initial = self.instance.version.product_id
            self.populate(self.instance.version.product_id)
        # GET request for add view
        else:
            self.populate(-1)

    def populate(self, product_id):
        if product_id:
            self.fields["version"].queryset = Version.objects.filter(
                product_id=product_id
            )
        else:
            self.fields["version"].queryset = Version.objects.all()


class BuildAdmin(admin.ModelAdmin):
    search_fields = ("name", "id")
    list_display = ("id", "name", "version", "product_name", "is_active")
    list_filter = ("version__product", "version", "is_active")

    form = BuildAdminForm
    fieldsets = [
        (
            "",
            {
                "fields": ("product", "version", "name", "is_active"),
            },
        ),
    ]

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
