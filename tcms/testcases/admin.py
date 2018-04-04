# pylint: disable=no-self-use
import inspect

from django import forms
from django.contrib import admin
from django.forms.widgets import Select

from tcms.issuetracker import types
from tcms.testcases.models import BugSystem
from tcms.testcases.models import Category


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
        trackers = []
        for module_object in types.__dict__.values():
            if inspect.isclass(module_object) and \
               issubclass(module_object, types.IssueTrackerType) and \
               module_object != types.IssueTrackerType:  # flake8: noqa
                trackers.append(module_object.__name__)
        return (('', ''), ) + tuple(zip(trackers, trackers))


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
        model = BugSystem
        fields = '__all__'


class BugSystemAdmin(admin.ModelAdmin):
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
admin.site.register(BugSystem, BugSystemAdmin)
