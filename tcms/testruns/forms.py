# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model

from tcms.core.forms.fields import UserField
from tcms.core.utils import string_to_list
from tcms.management.models import Build, Product, Version
from tcms.rpc.api.forms import DateTimeField
from tcms.testcases.models import TestCase
from tcms.testruns.models import TestRun

User = get_user_model()  # pylint: disable=invalid-name


class NewRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        exclude = ("tag", "cc")  # pylint: disable=modelform-uses-exclude

    manager = UserField()
    default_tester = UserField(required=False)
    start_date = DateTimeField(required=False)
    stop_date = DateTimeField(required=False)
    planned_start = DateTimeField(required=False)
    planned_stop = DateTimeField(required=False)

    case = forms.ModelMultipleChoiceField(
        queryset=TestCase.objects.none(),
        required=False,
    )

    def populate(self, plan_id):
        # plan is ModelChoiceField which contains all the plans
        # as we need only the plan for current run we filter the queryset
        self.fields["plan"].queryset = self.fields["plan"].queryset.filter(pk=plan_id)

        # reusing version from plan b/c TestRun.product_version is scheduled for removal
        # vvv allow modifying an immutable QueryDict.
        if hasattr(self.data, "_mutable"):
            self.data._mutable = True  # pylint: disable=protected-access
        self.data["product_version"] = (
            self.fields["plan"].queryset.first().product_version_id
        )
        if hasattr(self.data, "_mutable"):
            self.data._mutable = False  # pylint: disable=protected-access

        self.fields["product_version"].queryset = Version.objects.filter(
            pk=self.fields["plan"].queryset.first().product_version_id
        )

        self.fields["build"].queryset = Build.objects.filter(
            version_id=self.fields["plan"].queryset.first().product_version_id,
            is_active=True,
        )
        self.fields["case"].queryset = TestCase.objects.filter(
            case_status__is_confirmed=True
        ).all()


class SearchRunForm(forms.Form):
    """
    Includes *only* fields used in search.html b/c
    the actual search is now done via JSON RPC.
    """

    plan = forms.CharField(required=False)
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False)
    product_version = forms.ModelChoiceField(
        queryset=Version.objects.none(), required=False
    )
    build = forms.ModelChoiceField(
        queryset=Build.objects.none(),
        required=False,
    )
    default_tester = UserField(required=False)
    tag__name__in = forms.CharField(required=False)
    running = forms.IntegerField(required=False)

    def clean_tag__name__in(self):
        return string_to_list(self.cleaned_data["tag__name__in"])

    def populate(self, product_id=None):
        if product_id:
            self.fields["product_version"].queryset = Version.objects.filter(
                product__pk=product_id
            )
            self.fields["build"].queryset = Build.objects.filter(
                version__product=product_id
            )
