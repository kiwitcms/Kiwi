from django.forms import CharField, ModelChoiceField

from tcms.management.models import Product, Version
from tcms.testplans import forms as testplan_forms
from tcms.testplans.models import PlanType


# todo: this needs to become a model form with none of the fields required
class NewPlanForm(testplan_forms.NewPlanForm):
    pass


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
