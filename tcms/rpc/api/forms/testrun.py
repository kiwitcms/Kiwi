from django import forms
from django.contrib.auth import get_user_model

from tcms.core.forms.fields import UserField
from tcms.management.models import Build
from tcms.rpc.api.forms import UpdateModelFormMixin, DateTimeField
from tcms.testruns.models import TestRun, TestExecution

User = get_user_model()  # pylint: disable=invalid-name


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


class UpdateExecutionForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = '__all__'

    assignee = UserField()
    tested_by = UserField()
    close_date = DateTimeField()
