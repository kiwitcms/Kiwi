# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model

from tcms.core.forms.fields import UserField
from tcms.core.utils import string_to_list
from tcms.management.models import Build, Product, Version
from tcms.testcases.models import TestCase
from .models import TestRun

User = get_user_model()  # pylint: disable=invalid-name


class BaseRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = ['notes', 'default_tester', 'build', 'manager', 'summary']

    manager = UserField()
    default_tester = UserField(required=False)

    def populate(self, product_id):
        self.fields['build'].queryset = Build.objects.filter(product_id=product_id, is_active=True)


class NewRunForm(BaseRunForm):
    case = forms.ModelMultipleChoiceField(
        queryset=TestCase.objects.filter(case_status__id=2).all(),
    )


# =========== Forms for search/filter ==============

class SearchRunForm(forms.Form):
    """
        Includes *only* fields used in search.html b/c
        the actual search is now done via JSON RPC.
    """
    plan = forms.CharField(required=False)
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False
    )
    product_version = forms.ModelChoiceField(
        queryset=Version.objects.none(),
        required=False
    )
    build = forms.ModelChoiceField(
        queryset=Build.objects.none(),
        required=False,
    )
    default_tester = UserField(required=False)
    tag__name__in = forms.CharField(required=False)

    def clean_tag__name__in(self):
        return string_to_list(self.cleaned_data['tag__name__in'])

    def populate(self, product_id=None):
        if product_id:
            self.fields['product_version'].queryset = Version.objects.filter(
                product__pk=product_id
            )
            self.fields['build'].queryset = Build.objects.filter(
                product__pk=product_id
            )
