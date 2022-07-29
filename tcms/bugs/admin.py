# pylint: disable=no-self-use

from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from tcms.bugs.models import Bug, Severity
from tcms.core.admin import ObjectPermissionsAdminMixin
from tcms.core.history import ReadOnlyHistoryAdmin


class BugAdmin(ObjectPermissionsAdminMixin, ReadOnlyHistoryAdmin):
    def add_view(self, request, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("bugs-new"))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("bugs-get", args=[object_id]))


class SeverityAdmin(admin.ModelAdmin):
    list_display = ("id", "visual_icon", "name", "colored_color", "weight")
    ordering = ["-weight"]

    def colored_color(self, record):
        return format_html(
            """
            <span style="background-color: {}; height: 20px; display: block;
                         color: black; font-weight: bold">
                {}
            </span>
            """,
            record.color,
            record.color,
        )

    colored_color.short_description = "color"

    def visual_icon(self, record):
        return format_html(
            """
            <span class="{}" style="font-size: 18px; color: {};"></span>
            """,
            record.icon,
            record.color,
        )

    visual_icon.short_description = "icon"


admin.site.register(Bug, BugAdmin)
admin.site.register(Severity, SeverityAdmin)
