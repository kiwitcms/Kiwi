from django import forms

from tcms.management.models import Build
from tcms.rpc.api.forms import UpdateModelFormMixin


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = "__all__"


class UpdateForm(UpdateModelFormMixin, BuildForm):  # pylint: disable=remove-empty-class
    pass
