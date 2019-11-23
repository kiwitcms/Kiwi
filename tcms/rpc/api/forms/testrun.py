from django import forms
from django.utils.translation import ugettext_lazy as _

from tcms.management.models import Product, Version, Build
from tcms.testplans.models import TestPlan
from tcms.testruns.forms import BaseRunForm

from django.contrib.auth import get_user_model

User = get_user_model()  # pylint: disable=invalid-name


class XMLRPCNewRunForm(BaseRunForm):
    plan = forms.ModelChoiceField(
        queryset=TestPlan.objects.none(),
    )

    def assign_plan(self, plan_id):
        self.fields['plan'].queryset = TestPlan.objects.filter(pk=plan_id)
        self.populate(self.fields['plan'].queryset.first().product_id)


class XMLRPCUpdateRunForm(XMLRPCNewRunForm):
    plan = forms.ModelChoiceField(
        queryset=TestPlan.objects.all(),
        required=False,
    )
    summary = forms.CharField(
        required=False
    )
    manager = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None, required=False
    )
    product_version = forms.ModelChoiceField(
        queryset=Version.objects.none(),
        empty_label=None, required=False
    )
    build = forms.ModelChoiceField(
        queryset=Build.objects.all(),
        required=False
    )
    stop_date = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%d'],
        error_messages={
            'invalid': _('The stop date is invalid. The valid format is YYYY-MM-DD.')
        }
    )

    def clean_status(self):
        return self.cleaned_data.get('status')
