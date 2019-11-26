# -*- coding: utf-8 -*-

from django.forms.widgets import CheckboxInput as DjangoCheckboxInput

from tcms.rpc.utils import parse_bool_value


class CheckboxInput(DjangoCheckboxInput):
    def value_from_datadict(self, data, files, name):
        if name not in data:
            return False
        value = parse_bool_value(data.get(name))
        return value
