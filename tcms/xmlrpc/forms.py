# -*- coding: utf-8 -*-

from django.forms import BooleanField, CharField, ModelChoiceField
from django.forms.widgets import CheckboxInput

from tcms.management.models import Product, Version
from tcms.testcases.forms import XMLRPCNewCaseForm
from tcms.testcases.forms import XMLRPCUpdateCaseForm
from tcms.testplans.forms import NewPlanForm
from tcms.testplans.models import PlanType
from tcms.xmlrpc.utils import parse_bool_value


class XMLRPCCheckboxInput(CheckboxInput):
    def value_from_datadict(self, data, files, name):
        if name not in data:
            return False
        value = parse_bool_value(data.get(name))
        return value


class NewCaseForm(XMLRPCNewCaseForm):
    is_automated_proposed = BooleanField(label='Autoproposed',
                                         required=False,
                                         widget=XMLRPCCheckboxInput)


class UpdateCaseForm(XMLRPCUpdateCaseForm):
    is_automated_proposed = BooleanField(label='Autoproposed',
                                         required=False,
                                         widget=XMLRPCCheckboxInput)


class BasePlanForm(NewPlanForm):
    is_active = BooleanField(
        label="Active",
        required=False,
        widget=XMLRPCCheckboxInput
    )


class NewPlanForm(BasePlanForm):
    text = CharField()


class EditPlanForm(BasePlanForm):
    name = CharField(
        label="Plan name", required=False
    )
    type = ModelChoiceField(
        label="Type",
        queryset=PlanType.objects.all(),
        required=False
    )
    product = ModelChoiceField(
        label="Product",
        queryset=Product.objects.all(),
        required=False,
    )
    product_version = ModelChoiceField(
        label="Product Version",
        queryset=Version.objects.none(),
        required=False
    )
