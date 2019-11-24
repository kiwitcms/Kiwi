from django import forms

from tcms.management.models import Priority, Product
from tcms.testcases.forms import BaseCaseForm
from tcms.testcases.models import Category


class UpdateForm(BaseCaseForm):
    summary = forms.CharField(
        required=False,
    )
    priority = forms.ModelChoiceField(
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
