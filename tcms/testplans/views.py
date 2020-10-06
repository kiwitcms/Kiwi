# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import permission_required
from django.db.models import Count
from django.http import (HttpResponsePermanentRedirect,
                         HttpResponseRedirect)
from django.test import modify_settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from guardian.decorators import permission_required as object_permission_required

from uuslug import slugify

from tcms.core.forms import SimpleCommentForm
from tcms.core.response import ModifySettingsTemplateResponse
from tcms.testplans.forms import ClonePlanForm, NewPlanForm, PlanNotifyFormSet, SearchPlanForm
from tcms.testplans.models import PlanType, TestPlan
from tcms.testcases.models import TestCaseStatus
from tcms.management.models import Priority


@method_decorator(permission_required('testplans.add_testplan'), name='dispatch')
class NewTestPlanView(CreateView):
    model = TestPlan
    form_class = NewPlanForm
    template_name = 'testplans/mutable.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # clear fields which are set dynamically via JavaScript
        form.populate(self.request.POST.get('product', -1))
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial']['author'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notify_formset'] = kwargs.get('notify_formset') or PlanNotifyFormSet()
        return context

    def form_valid(self, form):
        notify_formset = PlanNotifyFormSet(self.request.POST)
        if notify_formset.is_valid():
            test_plan = form.save()
            notify_formset.instance = test_plan
            notify_formset.save()

            return HttpResponseRedirect(test_plan.get_absolute_url())

        # taken from FormMixin.form_invalid()
        return self.render_to_response(self.get_context_data(notify_formset=notify_formset))


@method_decorator(
    object_permission_required('testplans.change_testplan', (TestPlan, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class Edit(UpdateView):
    model = TestPlan
    form_class = NewPlanForm
    template_name = 'testplans/mutable.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.POST.get('product'):
            form.populate(product_id=self.request.POST['product'])
        else:
            form.populate(product_id=self.object.product_id)
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notify_formset'] = kwargs.get('notify_formset') or \
            PlanNotifyFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        notify_formset = PlanNotifyFormSet(self.request.POST, instance=self.object)
        if notify_formset.is_valid():
            notify_formset.save()
            return super().form_valid(form)

        # taken from FormMixin.form_invalid()
        context_data = self.get_context_data(form=form, notify_formset=notify_formset)
        return self.render_to_response(context_data)

    def form_invalid(self, form):
        notify_formset = PlanNotifyFormSet(self.request.POST, instance=self.object)
        context_data = self.get_context_data(form=form, notify_formset=notify_formset)
        return self.render_to_response(context_data)


@method_decorator(permission_required('testplans.view_testplan'), name='dispatch')
class SearchTestPlanView(TemplateView):

    template_name = 'testplans/search.html'

    def get_context_data(self, **kwargs):
        form = SearchPlanForm(self.request.GET)
        form.populate(product_id=self.request.GET.get('product'))

        context_data = {
            'form': form,
            'plan_types': PlanType.objects.all().only('pk', 'name').order_by('name'),
        }

        return context_data


# todo: this may still be used depending on how we design TP tree view
def get_number_of_children_plans(plan_ids):
    """Get the number of children plans related to each plan

    :param plan_ids: a tuple or list of TestPlans' ids
    :type plan_ids: list or tuple

    :return: a dict where key is plan_id and the value is the
        total count.
    :rtype: dict
    """
    query_set = TestPlan.objects.filter(parent__in=plan_ids).values('parent').annotate(
        total_count=Count('parent')).order_by('-parent')
    number_of_children_plans = {}
    for item in query_set:
        number_of_children_plans[item['parent']] = item['total_count']

    return number_of_children_plans


@method_decorator(
    object_permission_required('testplans.view_testplan', (TestPlan, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class TestPlanGetView(DetailView):

    template_name = 'testplans/get.html'
    http_method_names = ['get']
    model = TestPlan
    response_class = ModifySettingsTemplateResponse

    def render_to_response(self, context, **response_kwargs):
        self.response_class.modify_settings = modify_settings(
            MENU_ITEMS={'append': [
                ('...', [
                    (
                        _('Edit'),
                        reverse('plan-edit', args=[self.object.pk])
                    ),
                    (
                        _('Clone'),
                        reverse('plans-clone', args=[self.object.pk])
                    ),
                    (
                        _('History'),
                        "/admin/testplans/testplan/%d/history/" % self.object.pk
                    ),
                    ('-', '-'),
                    (
                        _('Object permissions'),
                        reverse('admin:testplans_testplan_permissions', args=[self.object.pk])
                    ),
                    ('-', '-'),
                    (
                        _('Delete'),
                        reverse('admin:testplans_testplan_delete', args=[self.object.pk])
                    )])]}
        )
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statues'] = TestCaseStatus.objects.all()
        context['priorities'] = Priority.objects.filter(is_active=True)
        context['comment_form'] = SimpleCommentForm()
        # todo: this can be passed to the new template and consumed
        # in the JavaScript when rendering test cases based on status
        # confirmed_status = TestCaseStatus.get_confirmed()
        return context


@method_decorator(
    object_permission_required('testplans.view_testplan', (TestPlan, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class GetTestPlanRedirectView(DetailView):

    http_method_names = ['get']
    model = TestPlan

    def get(self, request, *args, **kwargs):
        test_plan = self.get_object()
        return HttpResponsePermanentRedirect(reverse('test_plan_url',
                                                     args=[test_plan.pk,
                                                           slugify(test_plan.name)]))


@method_decorator(permission_required('testplans.add_testplan'), name='dispatch')
class Clone(FormView):
    template_name = 'testplans/clone.html'
    form_class = ClonePlanForm
    object = None

    def get(self, request, *args, **kwargs):
        self.object = TestPlan.objects.get(pk=kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = TestPlan.objects.get(pk=kwargs['pk'])
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.object
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.populate(self.object.product_id)
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial']['name'] = self.object.make_cloned_name()
        kwargs['initial']['product'] = self.object.product
        kwargs['initial']['version'] = self.object.product_version
        return kwargs

    def form_valid(self, form):
        form.cleaned_data['new_author'] = self.request.user
        cloned_plan = self.object.clone(**form.cleaned_data)

        return HttpResponseRedirect(
            reverse('test_plan_url_short', args=[cloned_plan.pk]))
