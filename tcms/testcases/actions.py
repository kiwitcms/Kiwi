# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.http import JsonResponse

from tcms.core.utils import form_errors_to_list
from tcms.testcases.forms import CaseCategoryForm
from tcms.testcases.forms import CaseComponentForm
from tcms.testcases.models import Category


__all__ = ('CategoryActions', 'ComponentActions')


class BaseActions(object):
    """Base class for all Actions"""

    def __init__(self, request):
        self.ajax_response = {'rc': 0, 'response': 'ok', 'errors_list': []}
        self.request = request
        self.product_id = request.POST.get('product')

    def _check_form_validation(self):
        form = self._get_form()
        if not form.is_valid():
            return 0, self.render_ajax(form_errors_to_list(form))

        return 1, form

    def get_testcases(self):
        from tcms.testcases.views import get_selected_testcases
        return get_selected_testcases(self.request)

    def render_ajax(self, data):
        """Return JSON response"""
        return JsonResponse(data)


class CategoryActions(BaseActions):
    """Category actions used by view function `category`"""

    def _get_form(self):
        self.form = CaseCategoryForm(self.request.POST)
        self.form.populate(product_id=self.product_id)
        return self.form

    def __check_perms(self, perm):
        return 1, True

    def update(self):
        is_valid, perm = self.__check_perms('change')
        if not is_valid:
            return perm

        is_valid, form = self._check_form_validation()
        if not is_valid:
            return form

        category_pk = self.request.POST.get('o_category')
        # FIXME: no exception hanlder when pk does not exist.
        category = Category.objects.get(pk=category_pk)
        # FIXME: lower performance. It's not necessary to update each TestCase
        # in this way.
        tcs = self.get_testcases()
        for tc in tcs:
            tc.category = category
            tc.save()
        return self.render_ajax(self.ajax_response)

    def render_form(self):
        form = CaseCategoryForm(initial={
            'product': self.product_id,
            'category': self.request.POST.get('o_category'),
        })
        form.populate(product_id=self.product_id)

        return HttpResponse(form.as_p())


class ComponentActions(BaseActions):
    """Component actions used by view function `component`"""

    def _get_form(self):
        self.form = CaseComponentForm(self.request.POST)
        self.form.populate(product_id=self.product_id)
        return self.form

    def __check_perms(self, perm):
        perm_name = 'testcases.{}_testcasecomponent'.format(perm)
        if not self.request.user.has_perm(perm_name):
            self.ajax_response['rc'] = 1
            self.ajax_response['response'] = 'Permission denied - ' + perm

            return 0, self.render_ajax(self.ajax_response)

        return 1, True

    def add(self):
        is_valid, perm = self.__check_perms('add')
        if not is_valid:
            return perm

        is_valid, form = self._check_form_validation()
        if not is_valid:
            return form

        test_cases = self.get_testcases()
        for test_case in test_cases:
            for component in form.cleaned_data['o_component']:
                try:
                    test_case.add_component(component=component)
                except Exception:
                    self.ajax_response['errors_list'].append({'case': test_case.pk,
                                                              'component': component.pk})

        return self.render_ajax(self.ajax_response)

    def remove(self):
        is_valid, perm = self.__check_perms('delete')
        if not is_valid:
            return perm

        is_valid, form = self._check_form_validation()
        if not is_valid:
            return form

        test_cases = self.get_testcases()
        for test_case in test_cases:
            for component in form.cleaned_data['o_component']:
                try:
                    test_case.remove_component(component=component)
                except Exception:
                    self.ajax_response['errors_list'].append({'case': test_case.pk,
                                                              'component': component.pk})

        return self.render_ajax(self.ajax_response)

    def update(self):
        is_valid, perm = self.__check_perms('change')
        if not is_valid:
            return perm

        is_valid, form = self._check_form_validation()
        if not is_valid:
            return form

        tcs = self.get_testcases()
        for tc in tcs:
            tc.clear_components()
            for c in form.cleaned_data['o_component']:
                tc.add_component(component=c)

        return self.render_ajax(self.ajax_response)

    def render_form(self):
        form = CaseComponentForm(initial={
            'product': self.product_id,
            'component': self.request.POST.getlist('o_component'),
        })
        form.populate(product_id=self.product_id)

        return HttpResponse(form.as_p())
