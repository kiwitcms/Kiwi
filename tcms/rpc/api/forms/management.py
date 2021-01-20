from django import forms

from tcms.management.models import Build, Product
from tcms.rpc.api.forms import UpdateModelFormMixin


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = "__all__"


class BuildUpdateForm(  # pylint: disable=remove-empty-class
    UpdateModelFormMixin, BuildForm
):
    pass


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
