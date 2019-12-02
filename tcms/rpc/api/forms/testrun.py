from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from tcms.management.models import Build, Product, Version
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.forms import BaseCaseRunForm, BaseRunForm
from tcms.testruns.models import TestExecutionStatus, TestRun

User = get_user_model()  # pylint: disable=invalid-name


class NewForm(BaseRunForm):
    plan = forms.ModelChoiceField(
        queryset=TestPlan.objects.none(),
    )

    def assign_plan(self, plan_id):
        self.fields['plan'].queryset = TestPlan.objects.filter(pk=plan_id)
        self.populate(self.fields['plan'].queryset.first().product_id)


class UpdateForm(NewForm):
    plan = forms.ModelChoiceField(
        queryset=TestPlan.objects.all(),
        required=False,
    )
    summary = forms.CharField(
        required=False
    )
    manager = forms.ModelChoiceField(
        queryset=User.objects.all(), required=False
    )
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None, required=False
    )
    product_version = forms.ModelChoiceField(
        queryset=Version.objects.none(),
        empty_label=None, required=False
    )
    build = forms.ModelChoiceField(
        queryset=Build.objects.all(),
        required=False
    )
    stop_date = forms.DateTimeField(
        required=False,
        input_formats=['%Y-%m-%d'],
        error_messages={
            'invalid': _('The stop date is invalid. The valid format is YYYY-MM-DD.')
        }
    )

    def clean_status(self):
        return self.cleaned_data.get('status')


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
            data = TestExecutionStatus.objects.get(name='IDLE')

        return data


class UpdateExecutionForm(BaseCaseRunForm):
    assignee = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    tested_by = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    build = forms.ModelChoiceField(queryset=Build.objects.all(), required=False)
