from django import forms
from django.contrib.auth import get_user_model

from tcms.management.models import Build
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.core.forms.fields import UserField
from tcms.testruns.forms import BaseCaseRunForm, BaseRunForm
from tcms.testruns.models import TestExecutionStatus, TestRun
from tcms.rpc.api.forms import UpdateModelFormMixin, DateTimeField

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


class NewExecutionForm(BaseCaseRunForm):
    assignee = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    run = forms.ModelChoiceField(queryset=TestRun.objects.all())
    case = forms.ModelChoiceField(queryset=TestCase.objects.all())

    def clean_assignee(self):
        data = self.cleaned_data.get('assignee')
        if not data:
            if self.cleaned_data.get('case') \
                    and self.cleaned_data['case'].default_tester_id:
                data = self.cleaned_data['case'].default_tester
            elif self.cleaned_data.get('run') \
                    and self.cleaned_data['run'].default_tester_id:
                data = self.cleaned_data['run'].default_tester

        return data

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


class UpdateExecutionForm(BaseCaseRunForm):
    tested_by = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    build = forms.ModelChoiceField(queryset=Build.objects.all(), required=False)
    case_text_version = forms.CharField(required=False)
