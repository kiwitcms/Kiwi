# -*- coding: utf-8 -*-
from django import forms
from django.forms import inlineformset_factory

from tcms.core.forms.fields import UserField
from tcms.core.widgets import SimpleMDE
from tcms.management.models import Product, Version
from tcms.testplans.models import TestPlan, TestPlanEmailSettings


class NewPlanForm(forms.ModelForm):
    class Meta:
        model = TestPlan
        exclude = ("tag",)  # pylint: disable=modelform-uses-exclude

    text = forms.CharField(widget=SimpleMDE(), required=False)

    def populate(self, product_id):
        if product_id:
            self.fields["product_version"].queryset = Version.objects.filter(
                product_id=product_id
            )
        else:
            self.fields["product_version"].queryset = Version.objects.all()


# note: these fields can't change during runtime !
_email_settings_fields = []  # pylint: disable=invalid-name
for field in TestPlanEmailSettings._meta.fields:
    _email_settings_fields.append(field.name)


# for usage in CreateView, UpdateView
PlanNotifyFormSet = inlineformset_factory(  # pylint: disable=invalid-name
    TestPlan,
    TestPlanEmailSettings,
    fields=_email_settings_fields,
    can_delete=False,
    can_order=False,
)


class SearchPlanForm(forms.ModelForm):
    class Meta:
        model = TestPlan
        fields = "__all__"

    # overriden widget
    author = UserField()

    # extra fields
    default_tester = UserField()

    def populate(self, product_id=None):
        if product_id:
            self.fields["product_version"].queryset = Version.objects.filter(
                product_id=product_id
            )
        else:
            self.fields["product_version"].queryset = Version.objects.none()


class ClonePlanForm(forms.Form):  # pylint: disable=must-inherit-from-model-form
    name = forms.CharField(required=True)

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None,
    )
    version = forms.ModelChoiceField(
        queryset=Version.objects.none(),
        empty_label=None,
    )

    copy_testcases = forms.BooleanField(required=False)
    set_parent = forms.BooleanField(required=False)

    def populate(self, product_pk):
        if product_pk:
            self.fields["version"].queryset = Version.objects.filter(
                product_id=product_pk
            )
        else:
            self.fields["version"].queryset = Version.objects.none()
