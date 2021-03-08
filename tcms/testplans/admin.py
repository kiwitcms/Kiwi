# -*- coding: utf-8 -*-
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse

from tcms.core.admin import ObjectPermissionsAdminMixin
from tcms.core.history import ReadOnlyHistoryAdmin
from tcms.testplans.models import PlanType, TestPlan


class PlanTypeAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name", "description")


class TestPlanAdmin(ObjectPermissionsAdminMixin, ReadOnlyHistoryAdmin):
    def add_view(self, request, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("plans-new"))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("test_plan_url_short", args=[object_id]))

    def response_delete(self, request, obj_display, obj_id):
        super().response_delete(request, obj_display, obj_id)
        return HttpResponseRedirect(reverse("core-views-index"))


admin.site.register(PlanType, PlanTypeAdmin)
admin.site.register(TestPlan, TestPlanAdmin)
