from django import forms

from tcms.core.contrib.linkreference.models import LinkReference


class LinkReferenceForm(forms.ModelForm):
    class Meta:
        model = LinkReference
        fields = "__all__"
