# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Count
from django.http import (HttpResponsePermanentRedirect,
                         HttpResponseRedirect, JsonResponse)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, View
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from guardian.decorators import permission_required as object_permission_required
from uuslug import slugify

from tcms.testcases.forms import QuickSearchCaseForm, SearchCaseForm
from tcms.testcases.models import TestCase, TestCasePlan, TestCaseStatus
from tcms.testcases.views import printable as testcases_printable
from tcms.testplans.forms import ClonePlanForm, NewPlanForm, PlanNotifyFormSet, SearchPlanForm
from tcms.testplans.models import PlanType, TestPlan
from tcms.testruns.models import TestRun


@method_decorator(permission_required('testplans.add_testplan'), name='dispatch')
class NewTestPlanView(CreateView):
    model = TestPlan
    form_class = NewPlanForm
    template_name = 'testplans/mutable.html'

    def get_form(self, form_class=None):
        form = super().get_form()
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
        form = super().get_form()
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


def get_number_of_plans_cases(plan_ids):
    """Get the number of cases related to each plan

    :param plan_ids: a tuple or list of TestPlans' ids
    :type plan_ids: list or tuple

    :return: a dict where key is plan_id and the value is the
        total count.
    :rtype: dict
    """
    query_set = TestCasePlan.objects.filter(plan__in=plan_ids).values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')

    number_of_plan_cases = {}
    for item in query_set:
        number_of_plan_cases[item['plan']] = item['total_count']

    return number_of_plan_cases


def get_number_of_plans_runs(plan_ids):
    """Get the number of runs related to each plan

    :param plan_ids: a tuple or list of TestPlans' ids
    :type plan_ids: list or tuple

    :return: a dict where key is plan_id and the value is the
        total count.
    :rtype: dict
    """
    query_set = TestRun.objects.filter(plan__in=plan_ids).values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    number_of_plan_runs = {}
    for item in query_set:
        number_of_plan_runs[item['plan']] = item['total_count']

    return number_of_plan_runs


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


def calculate_stats_for_testplans(plans):
    """Attach the number of cases and runs for each TestPlan

    :param plans: the queryset of TestPlans
    :type plans: dict
    :return: A list of TestPlans, each of which is attached the statistics which is
        with prefix cal meaning calculation result.
    :rtype: list
    """
    plan_ids = []
    for plan in plans:
        plan_ids.append(plan.pk)

    cases_counts = get_number_of_plans_cases(plan_ids)
    runs_counts = get_number_of_plans_runs(plan_ids)
    children_counts = get_number_of_children_plans(plan_ids)

    # Attach calculated statistics to each object of TestPlan
    for plan in plans:
        setattr(plan, 'cal_cases_count', cases_counts.get(plan.pk, 0))
        setattr(plan, 'cal_runs_count', runs_counts.get(plan.pk, 0))
        setattr(plan, 'cal_children_count', children_counts.get(plan.pk, 0))

    return plans


@method_decorator(
    object_permission_required('testplans.view_testplan', (TestPlan, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class TestPlanGetView(DetailView):

    template_name = 'plan/get.html'
    http_method_names = ['get']
    model = TestPlan

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        confirmed_status = TestCaseStatus.get_confirmed()
        context['review_case_count'] = self.object.case.exclude(
            case_status=confirmed_status).count()
        context['run_case_count'] = self.object.case.filter(
            case_status=confirmed_status).count()
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
class Clone(View):
    http_method_names = ['post']
    template_name = 'testplans/clone.html'

    def post(self, request):
        if 'plan' not in request.POST:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('TestPlan is required'))
            # redirect back where we came from
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        plan_id = request.POST.get('plan', 0)
        test_plan = get_object_or_404(TestPlan, pk=int(plan_id))

        post_data = request.POST.copy()
        if not request.POST.get('name'):
            post_data['name'] = test_plan.make_cloned_name()

        form = ClonePlanForm(post_data)
        form.populate(product_pk=request.POST.get('product'))

        # if required values are missing we are still going to show
        # the form below, otherwise clone & redirect
        if form.is_valid():
            form.cleaned_data['new_author'] = request.user
            cloned_plan = test_plan.clone(**form.cleaned_data)

            return HttpResponseRedirect(
                reverse('test_plan_url_short', args=[cloned_plan.pk]))

        # form wasn't valid
        context_data = {
            'test_plan': test_plan,
            'form': form,
        }

        return render(request, self.template_name, context_data)


@method_decorator(permission_required('testplans.change_testplan'), name='dispatch')
class ReorderCasesView(View):
    """Reorder cases"""

    http_method_names = ['post']

    def post(self, request, pk):
        if 'case' not in request.POST:
            return JsonResponse({
                'rc': 1,
                'response': 'At least one case is required to re-order.'
            })

        case_ids = []
        for case_id in request.POST.getlist('case'):
            case_ids.append(int(case_id))

        cases = TestCasePlan.objects.filter(case_id__in=case_ids, plan=pk).only('case_id')

        for case in cases:
            case.sortkey = (case_ids.index(case.case_id) + 1) * 10
            case.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})


@method_decorator(permission_required('testplans.change_testplan'), name='dispatch')
class UpdateParentView(View):
    """Updates TestPlan.parent. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        parent_id = int(request.POST.get('parent_id'))
        if parent_id == 0:
            parent_id = None

        child_ids = request.POST.getlist('child_ids[]')

        for child_pk in child_ids:
            test_plan = get_object_or_404(TestPlan, pk=int(child_pk))
            test_plan.parent_id = parent_id
            test_plan.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})


@method_decorator(permission_required('testcases.add_testcaseplan'), name='dispatch')
class LinkCasesView(View):
    """Link cases to plan"""

    def post(self, request, pk):
        plan = get_object_or_404(TestPlan.objects.only('pk'), pk=pk)

        case_ids = []
        for case_id in request.POST.getlist('case'):
            case_ids.append(int(case_id))

        cases = TestCase.objects.filter(pk__in=case_ids).only('pk')
        for case in cases:
            plan.add_case(case)

        return HttpResponseRedirect(reverse('test_plan_url', args=[pk, slugify(plan.name)]))


@method_decorator(permission_required('testcases.view_testcase'), name='dispatch')
class LinkCasesSearchView(View):
    """Search cases for linking to plan"""

    template_name = 'plan/search_case.html'

    def get(self, request, pk):
        plan = get_object_or_404(TestPlan, pk=pk)

        normal_form = SearchCaseForm(initial={
            'product': plan.product_id,
            'product_version': plan.product_version_id,
            'case_status_id': TestCaseStatus.get_confirmed()
        })
        quick_form = QuickSearchCaseForm()
        return render(self.request, self.template_name, {
            'search_form': normal_form,
            'quick_form': quick_form,
            'test_plan': plan,
        })

    def post(self, request, pk):
        plan = get_object_or_404(TestPlan, pk=pk)

        search_mode = request.POST.get('search_mode')
        if search_mode == 'quick':
            form = quick_form = QuickSearchCaseForm(request.POST)
            normal_form = SearchCaseForm()
        else:
            form = normal_form = SearchCaseForm(request.POST)
            form.populate(product_id=request.POST.get('product'))
            quick_form = QuickSearchCaseForm()

        cases = []
        if form.is_valid():
            cases = TestCase.list(form.cleaned_data)
            cases = cases.select_related(
                'author', 'default_tester', 'case_status', 'priority'
            ).only(
                'pk', 'summary', 'create_date', 'author__email',
                'default_tester__email', 'case_status__name',
                'priority__value'
            ).exclude(
                pk__in=plan.case.values_list('id', flat=True))

        context = {
            'test_plan': plan,
            'test_cases': cases,
            'search_form': normal_form,
            'quick_form': quick_form,
            'search_mode': search_mode
        }
        return render(request, self.template_name, context=context)


@require_POST
@permission_required('testplans.view_testplan')
def printable(request):
    """Create the printable copy for plan"""
    plan_pk = request.POST.get('plan', 0)

    if not plan_pk:
        messages.add_message(request,
                             messages.ERROR,
                             _('At least one test plan is required for print'))
        return HttpResponseRedirect(reverse('core-views-index'))

    try:
        TestPlan.objects.get(pk=plan_pk)
    except (ValueError, TestPlan.DoesNotExist):
        messages.add_message(request,
                             messages.ERROR,
                             _('Test Plan "%s" does not exist') % plan_pk)
        return HttpResponseRedirect(reverse('core-views-index'))

    # rendering is actually handled by testcases.views.printable()
    return testcases_printable(request)
