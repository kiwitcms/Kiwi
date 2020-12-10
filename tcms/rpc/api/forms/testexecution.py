from django import forms
from django.contrib.auth import get_user_model

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.forms.fields import UserField
from tcms.rpc.api.forms import UpdateModelFormMixin, DateTimeField
from tcms.testruns.models import TestExecution

User = get_user_model()  # pylint: disable=invalid-name


class UpdateExecutionForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestExecution
        fields = '__all__'

    assignee = UserField()
    tested_by = UserField()
    close_date = DateTimeField()


class AddExecutionLinkForm(forms.ModelForm):
    class Meta:
        model = LinkReference
        fields = '__all__'

    def populate(self, execution_id):
        self.fields['execution'].queryset = TestExecution.objects.filter(pk=execution_id)
