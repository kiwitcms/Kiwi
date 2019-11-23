# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

from tcms.core.utils import string_to_list
from tcms.core.forms.fields import UserField
from tcms.management.models import Product, Version, Build
from tcms.testplans.models import TestPlan
from tcms.testcases.models import TestCase
from .models import TestRun, TestExecutionStatus


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


class BaseCaseRunForm(forms.Form):
    build = forms.ModelChoiceField(queryset=Build.objects.all())
    status = forms.ModelChoiceField(queryset=TestExecutionStatus.objects.all(), required=False)
    assignee = UserField(required=False)
    case_text_version = forms.IntegerField(required=False)
    sortkey = forms.IntegerField(required=False)


class XMLRPCNewExecutionForm(BaseCaseRunForm):
    assignee = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    run = forms.ModelChoiceField(queryset=TestRun.objects.all())
    case = forms.ModelChoiceField(queryset=TestCase.objects.all())

    def clean_assignee(self):
        data = self.cleaned_data.get('assignee')
        if not data:
            if self.cleaned_data.get('case') \
                    and self.cleaned_data['case'].default_tester_id:
                data = self.cleaned_data['case'].default_tester
            elif self.cleaned_data.get('run') \
                    and self.cleaned_data['run'].default_tester_id:
                data = self.cleaned_data['run'].default_tester

        return data

    def clean_case_text_version(self):
        data = self.cleaned_data.get('case_text_version')
        if not data and self.cleaned_data.get('case'):
            data = self.cleaned_data['case'].history.latest().history_id

        return data

    def clean_status(self):
        data = self.cleaned_data.get('status')
        if not data:
            data = TestExecutionStatus.objects.get(name='IDLE')

        return data


class XMLRPCUpdateExecutionForm(BaseCaseRunForm):
    assignee = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    build = forms.ModelChoiceField(queryset=Build.objects.all(), required=False)
