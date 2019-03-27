# -*- coding: utf-8 -*-

from django.contrib import admin

from tcms.management.models import Classification
from tcms.management.models import Component, Version
from tcms.management.models import Priority
from tcms.management.models import Product
from tcms.management.models import Build, Tag


class ClassificationAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name')


class ProductsAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'classification', 'description')
    list_filter = ('id', 'name', 'classification')


class PriorityAdmin(admin.ModelAdmin):
    search_fields = ('value', 'id')
    list_display = ('id', 'value', 'is_active')
    list_filter = ('is_active', )


class ComponentAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'product', 'initial_owner', 'description')
    list_filter = ('product',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'initial_owner')


class VersionAdmin(admin.ModelAdmin):
    search_fields = ('value', 'id')
    list_display = ('id', 'product', 'value')
    list_filter = ('product',)


class BuildAdmin(admin.ModelAdmin):
    search_fields = ('name', 'build_id')
    list_display = ('build_id', 'name', 'product', 'is_active')
    list_filter = ('product',)


class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ('file_name', 'attachment_id')
    list_display = ('attachment_id', 'file_name', 'submitter', 'description',
                    'create_date', 'mime_type')


class TagAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name')


admin.site.register(Classification, ClassificationAdmin)
admin.site.register(Product, ProductsAdmin)
admin.site.register(Priority, PriorityAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(Build, BuildAdmin)
admin.site.register(Tag, TagAdmin)
