# -*- coding: utf-8 -*-

"""
Define forms for each request for validating request arguments
"""

from django import forms

from tcms.core.forms.fields import StripURLField


class AddLinkReferenceForm(forms.Form):
    """ Validate the argument within the request for adding new link """

    target_id = forms.IntegerField(
        error_messages={
            'required': 'target ID argument should appear in the request for '
                        'adding new link as long as the target argument.'})

    name = forms.CharField(
        max_length=64,  # same as the model
        error_messages={
            'required': 'You should name this new link.'})
    url = StripURLField(
        error_messages={
            'required': 'Missing URL.'})
