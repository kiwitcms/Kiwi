# -*- coding: utf-8 -*-
from django import forms

from django.utils.translation import ugettext_lazy as _

from tcms.core.widgets import SimpleMDE
from tcms.core.forms.fields import UserField, StripURLField
from tcms.core.utils import string_to_list
from tcms.testplans.models import TestPlan
from tcms.management.models import Priority, Product, Component
from tcms.testcases.models import TestCase, Category, TestCaseStatus
from tcms.testcases.fields import MultipleEmailField


ITEMS_PER_PAGE_CHOICES = (
    ('20', '20'),
    ('50', '50'),
    ('100', '100')
)

VALIDATION_ERROR_MESSAGE = _('Please input valid case id(s). '
                             'use comma to split more than one '
                             'case id. e.g. "111, 222"')


class BugField(forms.CharField):
    """
    Customizing forms CharFiled validation.
    Bug ID seperated using a delimiter such as comma.
    """

    def validate(self, value):
        super(BugField, self).validate(value)
        error = 'Enter a valid Bug ID.'
        bug_ids = string_to_list(value)

        for bug_id in bug_ids:
            try:
                bug_id = int(bug_id)
            except ValueError as error:
                raise forms.ValidationError(error)
            if abs(bug_id) > 8388607:
                raise forms.ValidationError(error)


# =========== Forms for create/update ==============

class BaseCaseForm(forms.Form):
    summary = forms.CharField(label="Summary", )
    default_tester = UserField(label="Default tester", required=False)
    requirement = forms.CharField(label="Requirement", required=False)
    is_automated = forms.BooleanField(initial=False, required=False)
    script = forms.CharField(label="Script", required=False)
    arguments = forms.CharField(label="Arguments", required=False)
    extra_link = StripURLField(
        label='Extra link',
        max_length=1024,
        required=False
    )
    # sortkey = forms.IntegerField(label = 'Sortkey', required = False)
    case_status = forms.ModelChoiceField(
        label="Case status",
        queryset=TestCaseStatus.objects.all(),
        empty_label=None,
        required=False
    )
    priority = forms.ModelChoiceField(
        label="Priority",
        queryset=Priority.objects.filter(is_active=True),
        empty_label=None,
    )
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        empty_label=None,
    )
    category = forms.ModelChoiceField(
        label="Category",
        queryset=Category.objects.none(),
        empty_label=None,
    )
    notes = forms.CharField(
        label='Notes',
        widget=forms.Textarea,
        required=False
    )
    text = forms.CharField(
        widget=SimpleMDE(),
        required=False,
        initial=_("""**Scenario**: ... what behavior will be tested ...
  **Given** ... conditions ...
  **When** ... actions ...
  **Then** ... expected results ...

*Actions*:

1. item
2. item
3. item

*Expected results*:

1. item
2. item
3. item
"""))

    def populate(self, product_id=None):
        if product_id:
            self.fields['category'].queryset = Category.objects.filter(
                product__id=product_id)
        else:
            self.fields['category'].queryset = Category.objects.all()


class NewCaseForm(BaseCaseForm):
    def clean_case_status(self):
        if not self.cleaned_data['case_status']:
            return TestCaseStatus.get_proposed()

        return self.cleaned_data['case_status']


class CaseNotifyForm(forms.Form):
    author = forms.BooleanField(required=False, initial=True)
    default_tester_of_case = forms.BooleanField(required=False, initial=True)
    managers_of_runs = forms.BooleanField(required=False, initial=True)
    default_testers_of_runs = forms.BooleanField(required=False, initial=True)
    assignees_of_case_runs = forms.BooleanField(required=False, initial=True)
    notify_on_case_update = forms.BooleanField(required=False, initial=True)
    notify_on_case_delete = forms.BooleanField(required=False, initial=True)

    cc_list = MultipleEmailField(
        required=False,
        label=u'CC to',
        help_text=u"""It will send notification email to each Email address
            within CC list. Email addresses within CC list are
            separated by comma.""",
        widget=forms.Textarea(attrs={'rows': 1, }))


# =========== Forms for  XML-RPC functions ==============


class XMLRPCBaseCaseForm(BaseCaseForm):
    pass


class XMLRPCNewCaseForm(XMLRPCBaseCaseForm):
    def clean_case_status(self):
        if not self.cleaned_data['case_status']:
            return TestCaseStatus.get_proposed()

        return self.cleaned_data['case_status']


class XMLRPCUpdateCaseForm(XMLRPCBaseCaseForm):
    summary = forms.CharField(
        label="Summary",
        required=False,
    )
    priority = forms.ModelChoiceField(
        label="Priority",
        queryset=Priority.objects.all(),
        empty_label=None,
        required=False,
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None,
        required=False,
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        empty_label=None,
        required=False,
    )


class BaseCaseSearchForm(forms.Form):
    summary = forms.CharField(required=False)
    author = forms.CharField(required=False)
    default_tester = forms.CharField(required=False)
    tag__name__in = forms.CharField(required=False)
    category = forms.ModelChoiceField(
        label="Category",
        queryset=Category.objects.none(),
        required=False
    )
    priority = forms.ModelMultipleChoiceField(
        label="Priority",
        queryset=Priority.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    case_status = forms.ModelMultipleChoiceField(
        label="Case status",
        queryset=TestCaseStatus.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    component = forms.ModelChoiceField(
        label="Components",
        queryset=Component.objects.none(),
        required=False
    )
    bug_id = BugField(label="Bug ID", required=False)
    is_automated = forms.BooleanField(required=False)
    items_per_page = forms.ChoiceField(label='Items per page',
                                       required=False,
                                       choices=ITEMS_PER_PAGE_CHOICES)

    def clean_bug_id(self):
        data = self.cleaned_data['bug_id']
        data = string_to_list(data)
        for data_obj in data:
            try:
                int(data_obj)
            except ValueError as error:
                raise forms.ValidationError(error)

        return data

    def clean_tag__name__in(self):
        return string_to_list(self.cleaned_data['tag__name__in'])

    def populate(self, product_id=None):
        """Limit the query to fit the plan"""
        if product_id:
            self.fields['category'].queryset = Category.objects.filter(
                product__id=product_id)
            self.fields['component'].queryset = Component.objects.filter(
                product__id=product_id)


# todo BaseCaseSearchForm is never used stand-alone and nothing else
# inherits from it so this class can be merged above
class SearchCaseForm(BaseCaseSearchForm):
    search = forms.CharField(required=False)
    # todo: is the plan field used ?
    plan = forms.CharField(required=False)
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        required=False
    )

    def clean_case_status(self):
        return list(self.cleaned_data['case_status'])

    def clean_priority(self):
        return list(self.cleaned_data['priority'])


class QuickSearchCaseForm(forms.Form):
    case_id_set = forms.CharField(required=False)

    def clean_case_id_set(self):
        case_id_set = self.cleaned_data['case_id_set']

        if not case_id_set:
            raise forms.ValidationError(VALIDATION_ERROR_MESSAGE)

        try:
            case_ids = []
            for case_id in case_id_set.split(','):
                case_ids.append(int(case_id))
            return case_ids
        except ValueError:
            raise forms.ValidationError(VALIDATION_ERROR_MESSAGE)


class CloneCaseForm(forms.Form):
    case = forms.ModelMultipleChoiceField(
        label='Test Case',
        queryset=TestCase.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    plan = forms.ModelMultipleChoiceField(
        label='Test Plan',
        queryset=TestPlan.objects.all(),
        widget=forms.CheckboxSelectMultiple()
    )
    copy_case = forms.BooleanField(
        label='Create a copy',
        help_text='Create a copy (Unchecking will create a link to selected '
                  'case)',
        required=False
    )
    maintain_case_orignal_author = forms.BooleanField(
        label='Keep original author',
        help_text='Keep original author (Unchecking will make me as author '
                  'of the copied test case)',
        required=False
    )
    maintain_case_orignal_default_tester = forms.BooleanField(
        label='Keep original default tester',
        help_text='Keep original default tester (Unchecking will make me as '
                  'default tester of the copied test case)',
        required=False
    )
    copy_component = forms.BooleanField(
        label='Copy test case components to the product of selected Test Plan',
        help_text='Copy test case components to the product of selected Test Plan ('
                  'Unchecking will remove components from copied test case)',
        required=False
    )

    def populate(self, case_ids):
        self.fields['case'].queryset = TestCase.objects.filter(case_id__in=case_ids)
