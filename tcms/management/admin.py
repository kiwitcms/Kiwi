# -*- coding: utf-8 -*-

from django.contrib import admin

from tcms.management.models import Classification
from tcms.management.models import Component, Version
from tcms.management.models import Priority
from tcms.management.models import Product
from tcms.management.models import TestBuild


class ClassificationAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'description')


class ProductsAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'classification', 'description')
    list_filter = ('id', 'name', 'classification')
    exclude = ('milestone_url', 'default_milestone', 'vote_super_user',
               'max_vote_super_bug')


class PriorityAdmin(admin.ModelAdmin):
    search_fields = ('value', 'id')
    list_display = ('id', 'value', 'sortkey', 'is_active')
    list_filter = ('is_active', )


class MilestoneAdmin(admin.ModelAdmin):
    search_fields = (('name', 'pk',))
    list_display = ('id', 'value', 'product', 'sortkey')
    list_filter = ('product', )


class ComponentAdmin(admin.ModelAdmin):
    search_fields = ('name', 'id')
    list_display = ('id', 'name', 'product', 'initial_owner', 'description')
    list_filter = ('product',)

    def get_queryset(self, request):
        qs = super(ComponentAdmin, self).get_queryset(request)
        return qs.select_related('product', 'initial_owner')


class VersionAdmin(admin.ModelAdmin):
    search_fields = ('value', 'id')
    list_display = ('id', 'product', 'value')
    list_filter = ('product',)


class BuildAdmin(admin.ModelAdmin):
    search_fields = ('name', 'build_id')
    list_display = ('build_id', 'name', 'product', 'is_active')
    list_filter = ('product',)
    exclude = ('milestone',)


class AttachmentAdmin(admin.ModelAdmin):
    search_fields = ('file_name', 'attachment_id')
    list_display = ('attachment_id', 'file_name', 'submitter', 'description',
                    'create_date', 'mime_type')


admin.site.register(Classification, ClassificationAdmin)
admin.site.register(Product, ProductsAdmin)
admin.site.register(Priority, PriorityAdmin)
admin.site.register(Component, ComponentAdmin)
admin.site.register(Version, VersionAdmin)
admin.site.register(TestBuild, BuildAdmin)
