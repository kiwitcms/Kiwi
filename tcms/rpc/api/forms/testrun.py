from django import forms
from django.contrib.auth import get_user_model

from tcms.core.forms.fields import UserField
from tcms.management.models import Build
from tcms.rpc.api.forms import DateTimeField, UpdateModelFormMixin
from tcms.testruns.models import (
    Environment,
    TestExecution,
    TestExecutionStatus,
    TestRun,
)

User = get_user_model()  # pylint: disable=invalid-name


class UpdateForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestRun
        exclude = ("tag", "cc")  # pylint: disable=modelform-uses-exclude

    manager = UserField()
    default_tester = UserField()
    start_date = DateTimeField()
    stop_date = DateTimeField()
    planned_start = DateTimeField()
    planned_stop = DateTimeField()

    def populate(self, version_id):
        self.fields["build"].queryset = Build.objects.filter(
            version_id=version_id, is_active=True
        )


class UpdateExecutionForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = "__all__"

    assignee = UserField()
    tested_by = UserField()
    stop_date = DateTimeField()
    start_date = DateTimeField()


class NewExecutionForm(forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = "__all__"

    assignee = UserField(required=False)
    tested_by = UserField(required=False)
    stop_date = DateTimeField(required=False)
    start_date = DateTimeField(required=False)


class UserForm(forms.Form):  # pylint: disable=must-inherit-from-model-form
    user = UserField()


class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment
        fields = "__all__"


class TestExecutionStatusForm(forms.ModelForm):
    class Meta:
        model = TestExecutionStatus
        fields = "__all__"
