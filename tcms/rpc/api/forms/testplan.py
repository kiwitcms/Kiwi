from django.forms import BooleanField, CharField, ModelChoiceField

from tcms.management.models import Product, Version
from tcms.rpc.forms import CheckboxInput
from tcms.testplans import forms as testplan_forms
from tcms.testplans.models import PlanType


class NewPlanForm(testplan_forms.NewPlanForm):
    is_active = BooleanField(
        required=False,
        widget=CheckboxInput
    )


class EditPlanForm(NewPlanForm):
    name = CharField(
        required=False
    )
    type = ModelChoiceField(
        queryset=PlanType.objects.all(),
        required=False
    )
    product = ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
    )
    product_version = ModelChoiceField(
        queryset=Version.objects.none(),
        required=False
    )
