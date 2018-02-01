# -*- coding: utf-8 -*-

from django.forms import BooleanField
from django.forms.widgets import CheckboxInput

from tcms.testcases.forms import XMLRPCNewCaseForm
from tcms.testcases.forms import XMLRPCUpdateCaseForm
from tcms.testplans.forms import XMLRPCNewPlanForm
from tcms.testplans.forms import XMLRPCEditPlanForm
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


class NewPlanForm(XMLRPCNewPlanForm):
    is_active = BooleanField(label="Active", required=False,
                             widget=XMLRPCCheckboxInput)


class EditPlanForm(XMLRPCEditPlanForm):
    is_active = BooleanField(label="Active", required=False,
                             widget=XMLRPCCheckboxInput)
