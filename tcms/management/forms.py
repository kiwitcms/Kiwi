# -*- coding: utf-8 -*-

from django import forms

from tcms.management.models import Version


class VersionForm(forms.ModelForm):
    class Meta:
        model = Version
        fields = ["product", "value"]
