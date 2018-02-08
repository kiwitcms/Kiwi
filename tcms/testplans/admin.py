# -*- coding: utf-8 -*-
from django.contrib import admin

from tcms.testplans.models import PlanType


class PlanTypeAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'description')


admin.site.register(PlanType, PlanTypeAdmin)
