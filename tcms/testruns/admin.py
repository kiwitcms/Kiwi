# pylint: disable=no-self-use
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from tcms.core.admin import ObjectPermissionsAdminMixin
from tcms.core.history import ReadOnlyHistoryAdmin
from tcms.testruns.models import Environment, TestExecutionStatus, TestRun


class TestRunAdmin(ObjectPermissionsAdminMixin, ReadOnlyHistoryAdmin):
    def add_view(self, request, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("admin:testruns_testrun_changelist"))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("testruns-get", args=[object_id]))

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        test_run = TestRun.objects.get(pk=object_id)
        if request.user.is_superuser or request.user in [
            test_run.manager,
            test_run.plan.author,
        ]:
            return super().delete_view(request, object_id, extra_context)

        messages.add_message(
            request,
            messages.ERROR,
            _("Permission denied: TestRun does not belong to you"),
        )
        return HttpResponseRedirect(reverse("testruns-get", args=[object_id]))


class TestExecutionStatusAdmin(admin.ModelAdmin):
    _for_more_info = _(
        """For more information about customizing test execution statuses see
        <a href="https://kiwitcms.readthedocs.io/en/latest/admin.html#test-execution-statuses">
        the documentation</a>!"""
    )
    list_display = ("id", "visual_icon", "name", "colored_color", "weight")
    ordering = ["-weight"]
    fieldsets = [
        (
            "",
            {
                "fields": ("name", "weight", "icon", "color"),
                "description": f"<h1>{_for_more_info}</h1>",
            },
        ),
    ]

    def colored_color(self, test_execution):
        return format_html(
            """
            <span style="background-color: {}; height: 20px; display: block;
                         color: black; font-weight: bold">
                {}
            </span>
            """,
            test_execution.color,
            test_execution.color,
        )

    colored_color.short_description = "color"

    def visual_icon(self, test_execution):
        return format_html(
            """
            <span class="{}" style="font-size: 18px; color: {};"></span>
            """,
            test_execution.icon,
            test_execution.color,
        )

    visual_icon.short_description = "icon"

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        obj = self.model.objects.get(pk=object_id)

        if obj.weight > 0:
            lookup = "weight__gt"
        elif obj.weight == 0:
            lookup = "weight"
        else:
            lookup = "weight__lt"

        if not self.model.objects.filter(**{lookup: 0}).exclude(pk=object_id).exists():
            messages.add_message(
                request,
                messages.ERROR,
                _("1 negative, 1 neutral & 1 positive status required!"),
            )

            return HttpResponseRedirect(
                reverse("admin:testruns_testexecutionstatus_changelist")
            )

        return super().delete_view(request, object_id, extra_context)


class EnvironmentAdmin(ObjectPermissionsAdminMixin, admin.ModelAdmin):
    _edit_properties_text = _("Edit properties")

    list_display = ("id", "name", "properties_link")
    search_fields = ("name",)

    def properties_link(self, obj):
        url = reverse("testruns-environment", args=[obj.id])
        return format_html(
            f"<a href='{url}'>{self._edit_properties_text}</a>",
        )

    properties_link.short_description = _("Properties")

    def response_change(self, request, obj):
        result = super().response_change(request, obj)

        if "_save" in request.POST:
            return HttpResponseRedirect(obj.get_absolute_url())
        return result


admin.site.register(TestRun, TestRunAdmin)
admin.site.register(TestExecutionStatus, TestExecutionStatusAdmin)
admin.site.register(Environment, EnvironmentAdmin)
