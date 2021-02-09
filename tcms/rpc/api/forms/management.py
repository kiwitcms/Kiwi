from django import forms

from tcms.management.models import Build, Component, Product
from tcms.rpc.api.forms import UpdateModelFormMixin


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = "__all__"


class BuildUpdateForm(  # pylint: disable=remove-empty-class
    UpdateModelFormMixin, BuildForm
):
    pass


class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = "__all__"


class ComponentUpdateForm(  # pylint: disable=remove-empty-class
    UpdateModelFormMixin, ComponentForm
):
    pass


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"
