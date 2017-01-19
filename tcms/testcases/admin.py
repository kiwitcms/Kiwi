# -*- coding: utf-8 -*-
from django.contrib import admin

from tcms.testcases.models import TestCaseCategory, TestCase
from tcms.testcases.models import TestCaseBugSystem


class TestCaseStatusAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'description')


class TestCaseCategoryAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'product', 'description')
    list_filter = ('product', )


class TestCaseAdmin(admin.ModelAdmin):
    search_fields = (('summary',))
    list_display = ('case_id', 'summary', 'category', 'author', 'case_status')
    list_filter = ('case_status', 'category')


class TestCaseBugSystemAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'url_reg_exp')


admin.site.register(TestCaseCategory, TestCaseCategoryAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(TestCaseBugSystem, TestCaseBugSystemAdmin)
