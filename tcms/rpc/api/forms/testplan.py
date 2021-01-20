from django import forms

from tcms.rpc.api.forms import UpdateModelFormMixin
from tcms.testplans.forms import NewPlanForm
from tcms.testplans.models import PlanType


class EditPlanForm(
    UpdateModelFormMixin, NewPlanForm
):  # pylint: disable=remove-empty-class
    pass


class PlanTypeForm(forms.ModelForm):
    class Meta:
        model = PlanType
        fields = "__all__"
