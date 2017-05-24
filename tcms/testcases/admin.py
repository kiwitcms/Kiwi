# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from django.forms.widgets import Select

from tcms.testcases import models
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCaseBugSystem
from tcms.testcases.models import TestCaseCategory
from tcms.testcases.models import TestCaseStatus


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


class IssueTrackerTypeSelectWidget(Select):
    """
    A select widget which displays the names of all classes
    derived from IssueTrackerType. Skip IssueTrackerType
    because it is doesn't provide implementations for most of its methods.
    """
    _choices = None

    def _types_as_choices(self):
        import inspect
        from tcms.issuetracker import types

        trackers = []
        for module_object in types.__dict__.values():
            if inspect.isclass(module_object) and \
               issubclass(module_object, types.IssueTrackerType) and \
               module_object != types.IssueTrackerType:  # flake8: noqa
                trackers.append(module_object.__name__)
        return (('', ''), ) + tuple(zip(trackers, trackers))

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


class IssueTrackerTypeField(forms.ChoiceField):
    """Special choice field which uses the widget above"""
    widget = IssueTrackerTypeSelectWidget

    def valid_value(self, value):
        return True


class BugSystemAdminForm(forms.ModelForm):
    # make password show asterisks
    api_password = forms.CharField(
        widget=forms.PasswordInput,
        label='API password or token',
        required=False
    )

    # select only tracker types for which we have available integrations
    tracker_type = IssueTrackerTypeField(
        label='Type',
        help_text='This determines how Nitrate integrates with the IT system',
    )

    class Meta:
        model = TestCaseBugSystem
        fields = '__all__'


class TestCaseBugSystemAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'url_reg_exp')
    form = BugSystemAdminForm


class TestCaseTextAdmin(admin.ModelAdmin):
    list_display = ('id', 'case')
    exclude = ('action_checksum', 'effect_checksum', 'setup_checksum', 'breakdown_checksum')


admin.site.register(TestCaseStatus, TestCaseStatusAdmin)
admin.site.register(TestCaseCategory, TestCaseCategoryAdmin)
admin.site.register(TestCase, TestCaseAdmin)
admin.site.register(TestCaseBugSystem, TestCaseBugSystemAdmin)
admin.site.register(models.TestCaseText, TestCaseTextAdmin)
