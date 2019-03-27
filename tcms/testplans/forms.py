# -*- coding: utf-8 -*-
from django import forms

from tcms.core.widgets import SimpleMDE
from tcms.core.utils import string_to_list
from tcms.core.forms.fields import StripURLField
from tcms.management.models import Product, Version
from .models import TestPlan, PlanType


class BasePlanForm(forms.Form):
    name = forms.CharField(
        label="Plan name",
        required=True
    )
    type = forms.ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        empty_label=None,
    )
    text = forms.CharField(
        label="Plan Document",
        widget=SimpleMDE(),
        required=False
    )
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        empty_label=None,
    )
    product_version = forms.ModelChoiceField(
        label="Product Version",
        queryset=Version.objects.none(),
        empty_label=None,
    )
    extra_link = StripURLField(
        label='Extra link',
        max_length=1024,
        required=False
    )
    parent = forms.IntegerField(required=False)

    def clean_parent(self):
        try:
            parent_pk = self.cleaned_data['parent']
            if parent_pk:
                return TestPlan.objects.get(pk=parent_pk)
        except TestPlan.DoesNotExist:
            raise forms.ValidationError('The plan does not exist in database.')
        return None

    def populate(self, product_id):
        if product_id:
            self.fields['product_version'].queryset = Version.objects.filter(
                product__id=product_id)
        else:
            self.fields['product_version'].queryset = Version.objects.all()


class NewPlanForm(BasePlanForm):

    auto_to_plan_author = forms.BooleanField(
        initial=True,
        required=False
    )
    auto_to_case_owner = forms.BooleanField(
        initial=True,
        required=False
    )
    auto_to_case_default_tester = forms.BooleanField(
        initial=True,
        required=False
    )
    notify_on_plan_update = forms.BooleanField(
        initial=True,
        required=False
    )
    notify_on_case_update = forms.BooleanField(
        initial=True,
        required=False
    )
    is_active = forms.BooleanField(required=False, initial=True)


# =========== Forms for search/filter ==============

class SearchPlanForm(forms.Form):
    pk = forms.IntegerField(required=False)
    pk__in = forms.CharField(required=False)
    parent__pk = forms.IntegerField(required=False)
    search = forms.CharField(label="Search", required=False)
    plan_id = forms.IntegerField(label="Plan ID", required=False)
    name__icontains = forms.CharField(label="Plan name", required=False)
    product = forms.ModelChoiceField(
        label="Product",
        queryset=Product.objects.all().order_by('name'),
        required=False
    )
    version = forms.ModelChoiceField(
        label="Product Version",
        queryset=Version.objects.none(),
        required=False
    )
    type = forms.ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        required=False,
    )
    author__username__startswith = forms.CharField(required=False)
    author__email__startswith = forms.CharField(required=False)
    case__default_tester__username__startswith = forms.CharField(
        required=False)
    tag__name__in = forms.CharField(required=False)
    is_active = forms.BooleanField(required=False)
    create_date__gte = forms.DateTimeField(
        label='Create after', required=False,
        widget=forms.DateInput(attrs={
            'class': 'vDateField',
        })
    )
    create_date__lte = forms.DateTimeField(
        label='Create before', required=False,
        widget=forms.DateInput(attrs={
            'class': 'vDateField',
        })
    )

    def clean_pk__in(self):
        results = []
        try:
            for result in string_to_list(self.cleaned_data['pk__in']):
                results.append(int(result))
        except Exception as error:
            raise forms.ValidationError(str(error))

        return results

    def clean_tag__name__in(self):
        return string_to_list(self.cleaned_data['tag__name__in'])

    def populate(self, product_id=None):
        if product_id:
            self.fields['version'].queryset = Version.objects.filter(
                product__id=product_id)
        else:
            self.fields['version'].queryset = Version.objects.none()


class ClonePlanForm(BasePlanForm):
    name = forms.CharField(label="Plan name", required=False)
    type = forms.ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        required=False,
    )
    keep_orignal_author = forms.BooleanField(
        label='Keep orignal author',
        help_text='Unchecking will make me the author of the copied plan',
        required=False,
    )
    link_testcases = forms.BooleanField(
        label='All Test Cases',
        required=False
    )
    copy_testcases = forms.BooleanField(
        label='Create a copy',
        help_text='Unchecking will create a link to selected plans',
        required=False
    )
    maintain_case_orignal_author = forms.BooleanField(
        label='Maintain original authors',
        help_text='Unchecking will make me the author of the copied cases',
        required=False
    )
    keep_case_default_tester = forms.BooleanField(
        label='Keep Default Tester',
        help_text='Unchecking will make me the default tester of copied cases',
        required=False
    )
    set_parent = forms.BooleanField(
        label='Set source plan as parent',
        help_text='Check it to set the source plan as parent of new cloned '
                  'plan.',
        required=False
    )
