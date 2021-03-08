# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth import get_user_model

from tcms.core.forms.fields import UserField
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

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        required=False,
    )

    def populate(self, plan_id):
        if plan_id:
            # plan is ModelChoiceField which contains all the plans
            # as we need only the plan for current run we filter the queryset
            self.fields["plan"].queryset = self.fields["plan"].queryset.filter(
                pk=plan_id
            )
            self.fields["product"].queryset = Product.objects.filter(
                pk=self.fields["plan"].queryset.first().product_id,
            )
            self.fields["build"].queryset = Build.objects.filter(
                version_id=self.fields["plan"].queryset.first().product_version_id,
                is_active=True,
            )
        else:
            # these are dynamically filtered via JavaScript
            self.fields["plan"].queryset = self.fields["plan"].queryset.none()
            self.fields["build"].queryset = Build.objects.none()

        self.fields["case"].queryset = TestCase.objects.filter(
            case_status__is_confirmed=True
        ).all()


class SearchRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = "__all__"

    # overriden widget
    manager = UserField()
    default_tester = UserField()

    # extra fields
    product = forms.ModelChoiceField(queryset=Product.objects.all(), required=False)
    version = forms.ModelChoiceField(queryset=Version.objects.none(), required=False)
    running = forms.IntegerField(required=False)

    def populate(self, product_id=None):
        if product_id:
            self.fields["version"].queryset = Version.objects.filter(
                product__pk=product_id
            )
            self.fields["build"].queryset = Build.objects.filter(
                version__product=product_id
            )
