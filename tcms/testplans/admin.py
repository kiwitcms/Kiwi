# -*- coding: utf-8 -*-
from django.contrib import admin

from tcms.testplans.models import TestPlanType
from tcms.testplans.models import TestPlan


class TestPlanTypeAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'description')


class TestPlanAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_filter = ['owner', 'create_date']
    list_display = ('name', 'create_date', 'owner', 'author', 'type')


admin.site.register(TestPlanType, TestPlanTypeAdmin)
admin.site.register(TestPlan, TestPlanAdmin)
