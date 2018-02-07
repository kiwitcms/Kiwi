# -*- coding: utf-8 -*-
from django import forms
from django.urls import reverse
from django.contrib import admin
from django.forms.widgets import Select
from django.http import HttpResponseRedirect

from tcms.testcases import views
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCaseText
from tcms.testcases.models import TestCaseBugSystem
from tcms.testcases.models import Category
from tcms.testcases.models import TestCaseStatus


class CategoryAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'product', 'description')
    list_filter = ('product', )


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
        widget=forms.PasswordInput(render_value=True),
        label='API password or token',
        required=False
    )

    # select only tracker types for which we have available integrations
    tracker_type = IssueTrackerTypeField(
        label='Type',
        help_text='This determines how Kiwi TCMS integrates with the IT system',
    )

    class Meta:
        model = TestCaseBugSystem
        fields = '__all__'


class TestCaseBugSystemAdmin(admin.ModelAdmin):
    search_fields = (('name',))
    list_display = ('id', 'name', 'url_reg_exp')
    fieldsets = [
        ('', {
            'fields': ('name', 'description', 'url_reg_exp', 'validate_reg_exp'),
        }),
        ('External Issue Tracker Integration', {
            'fields':('tracker_type', 'base_url', 'api_url', 'api_username', 'api_password'),
            'description': """<h1>Warning: read the
<a href="http://kiwitcms.readthedocs.io/en/latest/admin.html#configure-external-bug-trackers">
Configure external bug trackers</a> section before editting the values below!</h1>""",
        }),
    ]
    form = BugSystemAdminForm


admin.site.register(Category, CategoryAdmin)
admin.site.register(TestCaseBugSystem, TestCaseBugSystemAdmin)
