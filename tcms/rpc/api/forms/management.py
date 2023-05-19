from django import forms

from tcms.management.models import Build, Classification, Component, Product
from tcms.rpc.api.forms import UpdateModelFormMixin


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = "__all__"


class BuildUpdateForm(  # pylint: disable=remove-empty-class,too-many-ancestors
    UpdateModelFormMixin, BuildForm
):
    pass


class ComponentForm(forms.ModelForm):
    class Meta:
        model = Component
        fields = "__all__"


class ComponentUpdateForm(
    UpdateModelFormMixin, ComponentForm
):  # pylint: disable=remove-empty-class,too-many-ancestors
    pass


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "__all__"


class ClassificationForm(forms.ModelForm):
    class Meta:
        model = Classification
        fields = "__all__"
