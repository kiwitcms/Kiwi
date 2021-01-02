from django import forms

from tcms.management.models import Build


class BuildForm(forms.ModelForm):
    class Meta:
        model = Build
        fields = "__all__"
