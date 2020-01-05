from django import forms
from django.forms.utils import ErrorList

from tcms.testcases.models import TestCase


class UpdateForm(forms.ModelForm):
    class Meta:
        model = TestCase
        exclude = ('tag', 'component', 'plan')

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=None,
                 empty_permitted=False, instance=None, use_required_attribute=None,
                 renderer=None):
        super().__init__(
            data, files, auto_id, prefix,
            initial, error_class, label_suffix,
            empty_permitted, instance, use_required_attribute,
            renderer,
        )

        for field in self.fields:
            self.fields[field].required = False
