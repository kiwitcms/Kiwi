from django import forms

from tcms.core.forms.fields import UserField
from tcms.management.models import Build
from tcms.rpc.api.forms import DateTimeField, UpdateModelFormMixin
from tcms.testruns.models import (
    Environment,
    TestExecution,
    TestExecutionStatus,
    TestRun,
)


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


class NewExecutionForm(forms.ModelForm):
    class Meta:
        model = TestExecution
        exclude = ("tag",)  # pylint: disable=modelform-uses-exclude

    assignee = UserField(required=False)
    tested_by = UserField(required=False)
    stop_date = DateTimeField(required=False)
    start_date = DateTimeField(required=False)

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if (
            request
            and hasattr(request, "tenant")
            and request.tenant.schema_name != "public"
        ):
            tenant_users = request.tenant.authorized_users.all()
            self.fields["assignee"].queryset = tenant_users
            self.fields["tested_by"].queryset = tenant_users


class UpdateExecutionForm(  # pylint: disable=remove-empty-class,too-many-ancestors
    UpdateModelFormMixin, NewExecutionForm
):
    pass


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
