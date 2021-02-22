from django import forms
from django.contrib.auth import get_user_model

from tcms.core.forms.fields import UserField
from tcms.management.models import Build
from tcms.rpc.api.forms import DateTimeField, UpdateModelFormMixin
from tcms.testruns.models import TestExecution, TestRun

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


class UserForm(forms.Form):  # pylint: disable=must-inherit-from-model-form
    user = UserField()
