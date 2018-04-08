# -*- coding: utf-8 -*-
from django import forms

from tcms.core.helpers.cache import cached_entities
from tcms.management.models import Product, Build, Component, Version
from tcms.testcases.forms import BugField
from tcms.testcases.models import Category
from tcms.testplans.models import PlanType


def get_choice(value, _type=str, deli=','):
    """
    Used to clean a form field where multiple\n
    choices are seperated using a delimiter such as comma.\n
    Removing the empty value.
    """
    try:
        results = value.split(deli)
        return [_type(r.strip()) for r in results if r]
    except Exception as err:
        raise forms.ValidationError(str(err))


def get_boolean_choice(value):
    return {
        'yes': True,
        'no': False
    }.get(value, None)


class PlanForm(forms.Form):
    pl_type = forms.ModelMultipleChoiceField(
        required=False,
        queryset=PlanType.objects.all()
    )
    pl_summary = forms.CharField(required=False, max_length=200)
    pl_id = forms.CharField(required=False, max_length=200)
    pl_authors = forms.CharField(required=False, max_length=200)
    pl_owners = forms.CharField(required=False, max_length=200)
    pl_tags = forms.CharField(required=False, max_length=200)
    pl_tags_exclude = forms.BooleanField(required=False)
    pl_active = forms.CharField(required=False, max_length=200)
    pl_created_since = forms.DateField(required=False)
    pl_created_before = forms.DateField(required=False)
    pl_product = forms.ModelMultipleChoiceField(required=False, queryset=Product.objects.none())
    pl_component = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Component.objects.none()
    )
    pl_version = forms.ModelMultipleChoiceField(required=False, queryset=Version.objects.none())

    def clean_pl_active(self):
        return get_boolean_choice(self.cleaned_data['pl_active'])

    def clean_pl_id(self):
        return get_choice(self.cleaned_data['pl_id'], _type=int)

    def clean_pl_tags(self):
        return get_choice(self.cleaned_data['pl_tags'])

    def clean_pl_authors(self):
        return get_choice(self.cleaned_data['pl_authors'])

    def clean_pl_owners(self):
        return get_choice(self.cleaned_data['pl_owners'])

    def populate(self, data):
        prod_pks = data.getlist('pl_product')
        prod_pks = [k for k in prod_pks if k]
        if prod_pks:
            qs = Product.objects.filter(pk__in=prod_pks)
            self.fields['pl_product'].queryset = qs
        comp_pks = data.getlist('pl_component')
        comp_pks = [k for k in comp_pks if k]
        if comp_pks:
            qs = Component.objects.filter(pk__in=comp_pks)
            self.fields['pl_component'].queryset = qs
        ver_pks = data.getlist('pl_version')
        ver_pks = [k for k in ver_pks if k]
        if ver_pks:
            qs = Version.objects.filter(pk__in=ver_pks)
            self.fields['pl_version'].queryset = qs


class CaseForm(forms.Form):
    cs_id = forms.CharField(required=False, max_length=200)
    cs_summary = forms.CharField(required=False, max_length=200)
    cs_authors = forms.CharField(required=False, max_length=200)
    cs_tester = forms.CharField(required=False, max_length=200)
    cs_tags = forms.CharField(required=False, max_length=200)
    cs_bugs = BugField(required=False, max_length=200)
    cs_status = forms.MultipleChoiceField(required=False, choices=())
    cs_priority = forms.MultipleChoiceField(required=False, choices=())
    cs_auto = forms.CharField(required=False, max_length=200)
    cs_proposed = forms.CharField(required=False, max_length=200)
    cs_script = forms.CharField(required=False, max_length=200)
    cs_created_since = forms.DateField(required=False)
    cs_created_before = forms.DateField(required=False)
    cs_tags_exclude = forms.BooleanField(required=False)
    cs_product = forms.ModelMultipleChoiceField(required=False, queryset=Product.objects.none())
    cs_component = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Component.objects.none()
    )
    cs_category = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Category.objects.none()
    )

    def clean_cs_auto(self):
        return get_boolean_choice(self.cleaned_data['cs_auto'])

    def clean_cs_proposed(self):
        return get_boolean_choice(self.cleaned_data['cs_proposed'])

    def clean_cs_id(self):
        return get_choice(self.cleaned_data['cs_id'], _type=int)

    def clean_cs_authors(self):
        return get_choice(self.cleaned_data['cs_authors'])

    def clean_cs_bugs(self):
        return get_choice(self.cleaned_data['cs_bugs'], int)

    def clean_cs_tags(self):
        return get_choice(self.cleaned_data['cs_tags'])

    def clean_cs_tester(self):
        return get_choice(self.cleaned_data['cs_tester'])

    def populate(self, data):
        status_choice = [(s.pk, s.name) for s in cached_entities('TestCaseStatus')]
        self.fields['cs_status'].choices = status_choice

        priority_choice = [(p.pk, p.value) for p in cached_entities('Priority')]
        self.fields['cs_priority'].choices = priority_choice

        prod_pks = data.getlist('cs_product')
        prod_pks = [k for k in prod_pks if k]
        if prod_pks:
            qs = Product.objects.filter(pk__in=prod_pks)
            self.fields['cs_product'].queryset = qs
        comp_pks = data.getlist('cs_component')
        comp_pks = [k for k in comp_pks if k]
        if comp_pks:
            qs = Component.objects.filter(pk__in=comp_pks)
            self.fields['cs_component'].queryset = qs
        cat_pks = data.getlist('cs_category')
        cat_pks = [k for k in cat_pks if k]
        if cat_pks:
            qs = Category.objects.filter(pk__in=cat_pks)
            self.fields['cs_category'].queryset = qs


class RunForm(forms.Form):
    r_id = forms.CharField(required=False, max_length=200)
    r_summary = forms.CharField(required=False, max_length=200)
    r_manager = forms.CharField(required=False, max_length=200)
    r_tester = forms.CharField(required=False, max_length=200)
    r_tags = forms.CharField(required=False, max_length=200)
    r_tags_exclude = forms.BooleanField(required=False)
    r_env = forms.CharField(required=False, max_length=200)
    r_env_exclude = forms.BooleanField(required=False)
    r_running = forms.CharField(required=False, max_length=200)
    r_begin = forms.DateField(required=False)
    r_finished = forms.DateField(required=False)
    r_created_since = forms.DateField(required=False)
    r_created_before = forms.DateField(required=False)
    r_real_tester = forms.CharField(required=False, max_length=200)
    r_build = forms.ModelMultipleChoiceField(required=False, queryset=Build.objects.none())
    r_product = forms.ModelMultipleChoiceField(required=False, queryset=Product.objects.none())
    r_version = forms.ModelMultipleChoiceField(required=False, queryset=Version.objects.none())

    def clean_r_running(self):
        return get_boolean_choice(self.cleaned_data['r_running'])

    def clean_r_id(self):
        return get_choice(self.cleaned_data['r_id'], _type=int)

    def clean_r_tags(self):
        return get_choice(self.cleaned_data['r_tags'])

    def clean_r_env(self):
        return get_choice(self.cleaned_data['r_env'])

    def clean_r_tester(self):
        return get_choice(self.cleaned_data['r_tester'])

    def clean_r_real_tester(self):
        return get_choice(self.cleaned_data['r_real_tester'])

    def clean_r_manager(self):
        return get_choice(self.cleaned_data['r_manager'])

    def populate(self, data):
        prod_pks = data.getlist('r_product')
        prod_pks = [k for k in prod_pks if k]
        if prod_pks:
            qs = Product.objects.filter(pk__in=prod_pks).only('name')
            self.fields['r_product'].queryset = qs
        build_pks = data.getlist('r_build')
        build_pks = [k for k in build_pks if k]
        if build_pks:
            qs = Build.objects.filter(pk__in=build_pks).only('name')
            self.fields['r_build'].queryset = qs
        ver_pks = data.getlist('r_version')
        ver_pks = [k for k in ver_pks if k]
        if ver_pks:
            qs = Version.objects.filter(pk__in=ver_pks).only('value')
            self.fields['r_version'].queryset = qs
