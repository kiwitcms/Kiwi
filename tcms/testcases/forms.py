# -*- coding: utf-8 -*-
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _

from tcms.core.forms.fields import UserField
from tcms.core.widgets import DurationWidget, SimpleMDE
from tcms.management.models import Component, Priority, Product
from tcms.testcases.fields import MultipleEmailField
from tcms.testcases.models import (
    Category,
    TestCase,
    TestCaseEmailSettings,
    TestCaseStatus,
)
from tcms.testplans.models import TestPlan


class TestCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        exclude = [  # pylint: disable=modelform-uses-exclude
            "reviewer",
            "tag",
            "component",
            "plan",
        ]

    default_tester = UserField(required=False)
    priority = forms.ModelChoiceField(
        queryset=Priority.objects.filter(is_active=True),
        empty_label=None,
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None,
    )
    setup_duration = forms.DurationField(
        widget=DurationWidget(),
        required=False,
    )
    testing_duration = forms.DurationField(
        widget=DurationWidget(),
        required=False,
    )
    text = forms.CharField(
        widget=SimpleMDE(),
        required=False,
        initial=_(
            """**Scenario**: ... what behavior will be tested ...
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
3. item"""
        ),
    )

    def populate(self, product_id=None):
        if product_id:
            self.fields["category"].queryset = Category.objects.filter(
                product_id=product_id
            )
        else:
            self.fields["category"].queryset = Category.objects.all()


# only useful b/c we want to override the cc_list field
class CaseNotifyForm(forms.ModelForm):
    class Meta:
        model = TestCaseEmailSettings
        fields = "__all__"

    cc_list = MultipleEmailField(required=False)


# note: these fields can't change during runtime !
_email_settings_fields = []  # pylint: disable=invalid-name
for field in TestCaseEmailSettings._meta.fields:
    _email_settings_fields.append(field.name)


# for usage in CreateView, UpdateView
CaseNotifyFormSet = inlineformset_factory(  # pylint: disable=invalid-name
    TestCase,
    TestCaseEmailSettings,
    form=CaseNotifyForm,
    fields=_email_settings_fields,
    can_delete=False,
    can_order=False,
)


class SearchCaseForm(forms.ModelForm):
    class Meta:
        model = TestCase
        fields = "__all__"

    # overriden initial values
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.none(), required=False)
    component = forms.ModelChoiceField(
        queryset=Component.objects.none(), required=False
    )

    # overriden widgets
    priority = forms.ModelMultipleChoiceField(
        queryset=Priority.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )
    case_status = forms.ModelMultipleChoiceField(
        queryset=TestCaseStatus.objects.all(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    def populate(self, product_id=None):
        if product_id:
            self.fields["category"].queryset = Category.objects.filter(
                product_id=product_id
            )
            self.fields["component"].queryset = Component.objects.filter(
                product_id=product_id
            )


class CloneCaseForm(forms.Form):  # pylint: disable=must-inherit-from-model-form
    case = forms.ModelMultipleChoiceField(
        queryset=TestCase.objects.all(),
    )
    plan = forms.ModelMultipleChoiceField(
        queryset=TestPlan.objects.all(),
        required=False,
    )

    def populate(self, case_ids):
        self.fields["case"].queryset = TestCase.objects.filter(pk__in=case_ids)
        plan_ids = self.fields["case"].queryset.values_list("plan", flat=True)
        self.fields["plan"].queryset = TestPlan.objects.filter(pk__in=plan_ids)
