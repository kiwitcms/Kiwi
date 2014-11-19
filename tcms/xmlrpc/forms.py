# -*- coding: utf-8 -*-

from django.forms import Form
from django.forms import IntegerField
from django.forms import CharField
from django.forms import BooleanField
from django.forms import ValidationError
from django.forms.widgets import CheckboxInput

from tcms.core.exceptions import NitrateException
from tcms.core.utils.validations import validate_bug_id

from tcms.testcases.forms import XMLRPCNewCaseForm
from tcms.testcases.forms import XMLRPCUpdateCaseForm
from tcms.testplans.forms import XMLRPCNewPlanForm
from tcms.testplans.forms import XMLRPCEditPlanForm
from tcms.xmlrpc.utils import parse_bool_value


class AttachCaseBugForm(Form):
    case_id = IntegerField(required=True)
    bug_id = CharField(required=True)
    bug_system_id = IntegerField(required=True)
    summary = CharField(required=False)
    description = CharField(required=False)

    def clean(self):
        super(AttachCaseBugForm, self).clean()
        bug_id = self.cleaned_data['bug_id']
        bug_system_id = self.cleaned_data['bug_system_id']
        try:
            validate_bug_id(bug_id, bug_system_id)
        except NitrateException as e:
            raise ValidationError(str(e))

        return self.cleaned_data


class AttachCaseRunBugForm(Form):
    case_run_id = IntegerField(required=True)
    bug_id = CharField(required=True)
    bug_system_id = IntegerField(required=True)
    summary = CharField(required=False)
    description = CharField(required=False)

    def clean(self):
        super(AttachCaseRunBugForm, self).clean()
        bug_id = self.cleaned_data['bug_id']
        bug_system_id = self.cleaned_data['bug_system_id']
        try:
            validate_bug_id(bug_id, bug_system_id)
        except NitrateException as e:
            raise ValidationError(str(e))

        return self.cleaned_data


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
