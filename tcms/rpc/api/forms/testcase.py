from django import forms

from tcms.rpc.api.forms import UpdateModelFormMixin
from tcms.core.forms.fields import UserField
from tcms.testcases.models import TestCase


class NewForm(forms.ModelForm):
    class Meta:
        model = TestCase
        exclude = ('reviewer', 'tag', 'component', 'plan')  # pylint: disable=modelform-uses-exclude


class UpdateForm(UpdateModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestCase
        exclude = ('tag', 'component', 'plan')  # pylint: disable=modelform-uses-exclude

    default_tester = UserField()
    author = UserField()
    reviewer = UserField()
