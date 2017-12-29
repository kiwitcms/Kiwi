# -*- coding: utf-8 -*-

'''
Define forms for each request for validating request arguments
'''

from django import forms

from tcms.testruns.models import TestCaseRun
from tcms.core.forms.fields import StripURLField

__all__ = ('BasicValidationForm', 'AddLinkReferenceForm', )

LINKREF_TARGET = {
    'TestCaseRun': TestCaseRun,
}


class TargetCharField(forms.CharField):
    ''' Return clean Model class besides all of CharField '''

    default_error_messages = {
        'invalid_target':
            'Invalid target %(value)s. TCMS cannot determine the'
            ' model class according to this target.'}

    def __init__(self, targets={}, *args, **kwargs):
        super(TargetCharField, self).__init__(*args, **kwargs)

        self.targets = targets

    def clean(self, value):
        ''' Return the Model class object associated with the value '''

        super(TargetCharField, self).clean(value)
        model_class = self.targets.get(value, None)
        if model_class is None:
            raise forms.ValidationError(
                self.error_messages['invalid_target'] % {'value': value})
        return model_class


class BasicValidationForm(forms.Form):
    ''' Validate target and target ID basically '''

    target = TargetCharField(
        targets=LINKREF_TARGET,
        error_messages={
            'required': 'Due to miss the target argument, TCMS does not know '
                        'to which the new link will be linked.'})

    target_id = forms.IntegerField(
        error_messages={
            'required': 'target ID argument should appear in the request for '
                        'adding new link as long as the target argument.'})


class AddLinkReferenceForm(BasicValidationForm):
    ''' Validate the argument within the request for adding new link '''

    name = forms.CharField(
        max_length=64,  # same as the model
        error_messages={
            'required': 'You should name this new link.'})
    url = StripURLField(
        error_messages={
            'required': 'Missing URL.'})
