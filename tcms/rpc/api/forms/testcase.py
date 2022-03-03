from django import forms

from tcms.core.forms.fields import UserField
from tcms.rpc.api.forms import UpdateModelFormMixin
from tcms.testcases.models import Category, TestCase


class NewForm(forms.ModelForm):
    class Meta:
        model = TestCase
        exclude = (  # pylint: disable=modelform-uses-exclude
            "reviewer",
            "tag",
            "component",
            "plan",
        )


class UpdateForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestCase
        exclude = ("tag", "component", "plan")  # pylint: disable=modelform-uses-exclude

    default_tester = UserField()
    author = UserField()
    reviewer = UserField()


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
