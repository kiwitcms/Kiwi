from django import forms

from tcms.core.forms.fields import UserField
from tcms.rpc.api.forms import DateTimeFieldWithDefault, UpdateModelFormMixin
from tcms.testcases.models import (
    BugSystem,
    Category,
    Template,
    TestCase,
    TestCaseStatus,
)


class NewForm(forms.ModelForm):
    create_date = DateTimeFieldWithDefault(required=False)

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


class BugSystemForm(forms.ModelForm):
    class Meta:
        model = BugSystem
        fields = "__all__"


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"


class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = "__all__"


class TestCaseStatusForm(forms.ModelForm):
    class Meta:
        model = TestCaseStatus
        fields = "__all__"
