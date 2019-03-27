# -*- coding: utf-8 -*-

from django.forms.widgets import CheckboxInput

from tcms.testcases.forms import XMLRPCNewCaseForm
from tcms.testcases.forms import XMLRPCUpdateCaseForm
from tcms.xmlrpc.utils import parse_bool_value


class XMLRPCCheckboxInput(CheckboxInput):
    def value_from_datadict(self, data, files, name):
        if name not in data:
            return False
        value = parse_bool_value(data.get(name))
        return value


class NewCaseForm(XMLRPCNewCaseForm):
    pass


class UpdateCaseForm(XMLRPCUpdateCaseForm):
    pass
