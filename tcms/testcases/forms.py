# -*- coding: utf-8 -*-
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import ugettext_lazy as _

from tcms.core.forms.fields import StripURLField, UserField
from tcms.core.utils import string_to_list
from tcms.core.widgets import SimpleMDE
from tcms.management.models import Component, Priority, Product
from tcms.testcases.fields import MultipleEmailField
from tcms.testcases.models import Category, TestCase, TestCaseStatus, TestCaseEmailSettings
from tcms.testplans.models import TestPlan

ITEMS_PER_PAGE_CHOICES = (
    ('20', '20'),
    ('50', '50'),
    ('100', '100')
)

VALIDATION_ERROR_MESSAGE = _('Please input valid case id(s). '
                             'use comma to split more than one '
                             'case id. e.g. "111, 222"')


class BaseCaseForm(forms.Form):
    summary = forms.CharField()
    default_tester = UserField(required=False)
    requirement = forms.CharField(required=False)
    is_automated = forms.BooleanField(initial=False, required=False)
    script = forms.CharField(required=False)
    arguments = forms.CharField(required=False)
    extra_link = StripURLField(
        max_length=1024,
        required=False
    )
    # sortkey = forms.IntegerField(label = 'Sortkey', required = False)
    case_status = forms.ModelChoiceField(
        queryset=TestCaseStatus.objects.all(),
        empty_label=None,
        required=False
    )
    priority = forms.ModelChoiceField(
        queryset=Priority.objects.filter(is_active=True),
        empty_label=None,
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None,
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        empty_label=None,
    )
    notes = forms.CharField(
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
3. item"""))

    def populate(self, product_id=None):
        if product_id:
            self.fields['category'].queryset = Category.objects.filter(
                product_id=product_id)
        else:
            self.fields['category'].queryset = Category.objects.all()


class NewCaseForm(BaseCaseForm):
    def clean_case_status(self):
        if not self.cleaned_data['case_status']:
            return TestCaseStatus.get_proposed()

        return self.cleaned_data['case_status']


class EditCaseForm(forms.ModelForm):

    class Meta:
        model = TestCase
        exclude = ['reviewer', 'tag', 'component', 'plan']

    default_tester = UserField(required=False)
    priority = forms.ModelChoiceField(
        queryset=Priority.objects.filter(is_active=True),
        empty_label=None,
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None,
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
3. item"""))

    def populate(self, product_id=None):
        if product_id:
            self.fields['category'].queryset = Category.objects.filter(
                product_id=product_id)
        else:
            self.fields['category'].queryset = Category.objects.all()


# only useful b/c we want to override the cc_list field
class CaseNotifyForm(forms.ModelForm):
    class Meta:
        model = TestCaseEmailSettings
        exclude = ()

    cc_list = MultipleEmailField(required=False)


# for usage in CreateView, UpdateView
CaseNotifyFormSet = inlineformset_factory(
    TestCase,
    TestCaseEmailSettings,
    form=CaseNotifyForm,
    fields=[f.name for f in TestCaseEmailSettings._meta.fields],
    can_delete=False,
    can_order=False,
)


class BaseCaseSearchForm(forms.Form):
    summary = forms.CharField(required=False)
    author = forms.CharField(required=False)
    default_tester = forms.CharField(required=False)
    tag__name__in = forms.CharField(required=False)
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=False
    )
    priority = forms.ModelMultipleChoiceField(
        queryset=Priority.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    case_status = forms.ModelMultipleChoiceField(
        queryset=TestCaseStatus.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    component = forms.ModelChoiceField(
        queryset=Component.objects.none(),
        required=False
    )
    is_automated = forms.BooleanField(required=False)
    items_per_page = forms.ChoiceField(
        required=False,
        choices=ITEMS_PER_PAGE_CHOICES)

    def clean_tag__name__in(self):
        return string_to_list(self.cleaned_data['tag__name__in'])

    def populate(self, product_id=None):
        """Limit the query to fit the plan"""
        if product_id:
            self.fields['category'].queryset = Category.objects.filter(
                product_id=product_id)
            self.fields['component'].queryset = Component.objects.filter(
                product_id=product_id)


# todo BaseCaseSearchForm is never used stand-alone and nothing else
# inherits from it so this class can be merged above
class SearchCaseForm(BaseCaseSearchForm):
    search = forms.CharField(required=False)
    # todo: is the plan field used ?
    plan = forms.CharField(required=False)
    product = forms.ModelChoiceField(
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
        queryset=TestCase.objects.all(),
    )
    plan = forms.ModelMultipleChoiceField(
        queryset=TestPlan.objects.all(),
        required=False,
    )

    def populate(self, case_ids):
        self.fields['case'].queryset = TestCase.objects.filter(pk__in=case_ids)
        plan_ids = self.fields['case'].queryset.values_list('plan', flat=True)
        self.fields['plan'].queryset = TestPlan.objects.filter(pk__in=plan_ids)
