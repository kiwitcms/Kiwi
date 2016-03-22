# -*- coding: utf-8 -*-

from django.http import HttpResponse
import json

from tcms.core import forms
from tcms.testcases.forms import CaseCategoryForm
from tcms.testcases.forms import CaseComponentForm
from tcms.testcases.models import TestCaseCategory


__all__ = ('CategoryActions', 'ComponentActions')


class BaseActions(object):
    '''Base class for all Actions'''

    def __init__(self, request):
        self.ajax_response = {'rc': 0, 'response': 'ok', 'errors_list': []}
        self.request = request
        self.product_id = request.REQUEST.get('product')

    def get_testcases(self):
        from tcms.testcases.views import get_selected_testcases

        return get_selected_testcases(self.request)


class CategoryActions(BaseActions):
    '''Category actions used by view function `category`'''

    def __get_form(self):
        self.form = CaseCategoryForm(self.request.REQUEST)
        self.form.populate(product_id=self.product_id)
        return self.form

    def __check_form_validation(self):
        form = self.__get_form()
        if not form.is_valid():
            return 0, self.render_ajax(forms.errors_to_list(form))

        return 1, form

    def __check_perms(self, perm):
        return 1, True

    def update(self):
        is_valid, perm = self.__check_perms('change')
        if not is_valid:
            return perm

        is_valid, form = self.__check_form_validation()
        if not is_valid:
            return form

        category_pk = self.request.REQUEST.get('o_category')
        # FIXME: no exception hanlder when pk does not exist.
        category = TestCaseCategory.objects.get(pk=category_pk)
        # FIXME: lower performance. It's not necessary to update each TestCase
        # in this way.
        tcs = self.get_testcases()
        for tc in tcs:
            tc.category = category
            tc.save()
        return self.render_ajax(self.ajax_response)

    def render_ajax(self, response):
        return HttpResponse(json.dumps(self.ajax_response))

    def render_form(self):
        form = CaseCategoryForm(initial={
            'product': self.product_id,
            'category': self.request.REQUEST.get('o_category'),
        })
        form.populate(product_id=self.product_id)

        return HttpResponse(form.as_p())


class ComponentActions(BaseActions):
    '''Component actions used by view function `component`'''

    def __get_form(self):
        self.form = CaseComponentForm(self.request.REQUEST)
        self.form.populate(product_id=self.product_id)
        return self.form

    def __check_form_validation(self):
        form = self.__get_form()
        if not form.is_valid():
            return 0, self.render_ajax(forms.errors_to_list(form))

        return 1, form

    def __check_perms(self, perm):
        perm_name = 'testcases.' + perm + '_testcasecomponent'
        if not self.request.user.has_perm(perm_name):
            self.ajax_response['rc'] = 1
            self.ajax_response['response'] = 'Permission denied - ' + perm

            return 0, self.render_ajax(self.ajax_response)

        return 1, True

    def add(self):
        is_valid, perm = self.__check_perms('add')
        if not is_valid:
            return perm

        is_valid, form = self.__check_form_validation()
        if not is_valid:
            return form

        tcs = self.get_testcases()
        for tc in tcs:
            for c in form.cleaned_data['o_component']:
                try:
                    tc.add_component(component=c)
                except:
                    self.ajax_response['errors_list'].append({
                        'case': tc.pk, 'component': c.pk})

        return self.render_ajax(self.ajax_response)

    def remove(self):
        is_valid, perm = self.__check_perms('delete')
        if not is_valid:
            return perm

        is_valid, form = self.__check_form_validation()
        if not is_valid:
            return form

        tcs = self.get_testcases()
        for tc in tcs:
            for c in form.cleaned_data['o_component']:
                try:
                    tc.remove_component(component=c)
                except:
                    self.ajax_response['errors_list'].append({
                        'case': tc.pk, 'component': c.pk})

        return self.render_ajax(self.ajax_response)

    def update(self):
        is_valid, perm = self.__check_perms('change')
        if not is_valid:
            return perm

        is_valid, form = self.__check_form_validation()
        if not is_valid:
            return form

        # self.tcs.update(category = self.form.cleaned_data['category'])
        tcs = self.get_testcases()
        for tc in tcs:
            tc.clear_components()
            for c in form.cleaned_data['o_component']:
                tc.add_component(component=c)

        return self.render_ajax(self.ajax_response)

    def render_ajax(self, response):
        return HttpResponse(json.dumps(self.ajax_response))

    def render_form(self):
        form = CaseComponentForm(initial={
            'product': self.product_id,
            # 'category': self.request.REQUEST.get('category'),
            'component': self.request.REQUEST.getlist('o_component'),
        })
        form.populate(product_id=self.product_id)

        return HttpResponse(form.as_p())
