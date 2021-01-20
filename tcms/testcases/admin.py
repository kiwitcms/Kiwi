# pylint: disable=no-self-use

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.forms.widgets import Select
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from tcms.core.admin import ObjectPermissionsAdminMixin
from tcms.core.history import ReadOnlyHistoryAdmin
from tcms.testcases.models import BugSystem, Category, TestCase, TestCaseStatus


class TestCaseStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_confirmed")
    ordering = ["-is_confirmed", "id"]
    fieldsets = [
        (
            "",
            {
                "fields": ("name", "description", "is_confirmed"),
                "description": "<h1>%s</h1>"
                % _(
                    """For more information about customizing test case statuses see
        <a href="https://kiwitcms.readthedocs.io/en/latest/admin.html#test-case-statuses">
        the documentation</a>!"""
                ),
            },
        ),
    ]

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        obj = self.model.objects.get(pk=object_id)

        if (
            not self.model.objects.filter(is_confirmed=obj.is_confirmed)
            .exclude(pk=object_id)
            .exists()
        ):
            messages.add_message(
                request,
                messages.ERROR,
                _("1 confirmed & 1 uncomfirmed status required!"),
            )

            return HttpResponseRedirect(
                reverse("admin:testcases_testcasestatus_changelist")
            )

        return super().delete_view(request, object_id, extra_context)


class TestCaseAdmin(ObjectPermissionsAdminMixin, ReadOnlyHistoryAdmin):
    def add_view(self, request, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("testcases-new"))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return HttpResponseRedirect(reverse("testcases-get", args=[object_id]))


class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name", "product", "description")
    list_filter = ("product",)


class IssueTrackerTypeSelectWidget(Select):
    """
    A select widget which displays the names of all classes
    derived from IssueTrackerType. Skip IssueTrackerType
    because it is doesn't provide implementations for most of its methods.
    """

    _choices = None

    @property
    def choices(self):
        if self._choices is None:
            self._choices = self._types_as_choices()
        return self._choices

    @choices.setter
    def choices(self, _):
        # ChoiceField.__init__ sets ``self.choices = choices``
        # which would override ours.
        pass

    @staticmethod
    def _types_as_choices():
        return (("", ""),) + tuple(
            zip(settings.EXTERNAL_BUG_TRACKERS, settings.EXTERNAL_BUG_TRACKERS)
        )


class IssueTrackerTypeField(forms.ChoiceField):
    """Special choice field which uses the widget above"""

    widget = IssueTrackerTypeSelectWidget

    def valid_value(self, value):
        return True


class BugSystemAdminForm(forms.ModelForm):
    # make password show asterisks
    api_password = forms.CharField(
        widget=forms.PasswordInput(render_value=True), required=False
    )

    # select only tracker types for which we have available integrations
    tracker_type = IssueTrackerTypeField(  # pylint:disable=form-field-help-text-used
        help_text="This determines how Kiwi TCMS integrates with the IT system",
    )

    class Meta:
        model = BugSystem
        fields = "__all__"


class BugSystemAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("id", "name", "base_url")
    fieldsets = [
        (
            "",
            {
                "fields": ("name",),
            },
        ),
        (
            "External Issue Tracker Integration",
            {
                "fields": (
                    "tracker_type",
                    "base_url",
                    "api_url",
                    "api_username",
                    "api_password",
                ),
                "description": """<h1>Warning: read the
<a href="http://kiwitcms.readthedocs.io/en/latest/admin.html#configure-external-bug-trackers">
Configure external bug trackers</a> section before editting the values below!</h1>""",
            },
        ),
    ]
    form = BugSystemAdminForm


admin.site.register(BugSystem, BugSystemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(TestCaseStatus, TestCaseStatusAdmin)
