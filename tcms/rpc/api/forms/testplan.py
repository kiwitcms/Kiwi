from django import forms

from tcms.rpc.api.forms import DateTimeFieldWithDefault, UpdateModelFormMixin
from tcms.testplans.forms import NewPlanForm
from tcms.testplans.models import PlanType


class NewPlanAPIForm(NewPlanForm):
    create_date = DateTimeFieldWithDefault(required=False)


class EditPlanForm(
    UpdateModelFormMixin, NewPlanForm
):  # pylint: disable=remove-empty-class,too-many-ancestors
    pass


class PlanTypeForm(forms.ModelForm):
    class Meta:
        model = PlanType
        fields = "__all__"
