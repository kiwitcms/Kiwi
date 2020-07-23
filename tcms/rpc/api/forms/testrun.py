from django import forms
from django.contrib.auth import get_user_model

from tcms.core.forms.fields import UserField
from tcms.management.models import Build
from tcms.rpc.api.forms import UpdateModelFormMixin, DateTimeField
from tcms.testplans.models import TestPlan
from tcms.testruns.forms import BaseRunForm
from tcms.testruns.models import TestExecutionStatus, TestRun, TestExecution

User = get_user_model()  # pylint: disable=invalid-name


class NewForm(BaseRunForm):
    plan = forms.ModelChoiceField(
        queryset=TestPlan.objects.none(),
    )

    def assign_plan(self, plan_id):
        self.fields['plan'].queryset = TestPlan.objects.filter(pk=plan_id)
        self.populate(self.fields['plan'].queryset.first().product_id)


class UpdateForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestRun
        exclude = ('tag', 'cc')  # pylint: disable=modelform-uses-exclude

    manager = UserField()
    default_tester = UserField()
    start_date = DateTimeField()
    stop_date = DateTimeField()

    def populate(self, product_id):
        self.fields['build'].queryset = Build.objects.filter(product_id=product_id, is_active=True)


class NewTestExecutionForm(forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = '__all__'

    assignee = UserField(required=False)
    tested_by = UserField(required=False)

    def clean_case_text_version(self):
        data = self.cleaned_data.get('case_text_version')
        if not data and self.cleaned_data.get('case'):
            data = self.cleaned_data['case'].history.latest().history_id

        return data

    def clean_status(self):
        data = self.cleaned_data.get('status')
        if not data:
            data = TestExecutionStatus.objects.filter(weight=0).first()

        return data


class UpdateExecutionForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = '__all__'

    assignee = UserField()
    tested_by = UserField()
