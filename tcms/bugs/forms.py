# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django import forms
from django.utils.translation import gettext_lazy as _

from tcms.bugs.models import Bug
from tcms.core.forms.fields import UserField
from tcms.core.widgets import SimpleMDE
from tcms.management.models import Build, Version


class NewBugForm(forms.ModelForm):
    class Meta:
        model = Bug
        fields = ["summary", "assignee", "reporter", "product", "version", "build"]

    assignee = UserField(required=False)

    text = forms.CharField(
        widget=SimpleMDE(),
        required=False,
        initial=_(
            """Description of problem:


How often reproducible:


Steps to Reproduce:
1.
2.
3.

Actual results:


Expected results:


Additional info:"""
        ),
    )

    def populate(self, product_id=None):
        if product_id:
            self.fields["version"].queryset = Version.objects.filter(
                product_id=product_id
            )
            self.fields["build"].queryset = Build.objects.filter(
                version__product=product_id
            )
        else:
            self.fields["version"].queryset = Version.objects.all()
            self.fields["build"].queryset = Build.objects.all()


class BugCommentForm(forms.Form):  # pylint: disable=must-inherit-from-model-form
    bug = forms.ModelChoiceField(
        queryset=Bug.objects.all(),
    )

    text = forms.CharField(
        widget=SimpleMDE(),
        required=False,
    )

    def populate(self, bug_id):
        self.fields["bug"].queryset = Bug.objects.filter(pk=bug_id)
