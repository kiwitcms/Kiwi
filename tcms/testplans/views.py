# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import (Http404, HttpResponsePermanentRedirect,
                         HttpResponseRedirect)
from django.shortcuts import get_object_or_404, render
from django.test import modify_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, View
from django.views.generic.base import TemplateView
from uuslug import slugify

from tcms.core.response import ModifySettingsTemplateResponse
from tcms.testcases.models import TestCasePlan
from tcms.testplans.forms import ClonePlanForm, NewPlanForm, SearchPlanForm
from tcms.testplans.models import PlanType, TestPlan
from tcms.testruns.models import TestRun


def update_plan_email_settings(test_plan, form):
    """Update test plan's email settings"""
    test_plan.emailing.notify_on_plan_update = form.cleaned_data[
        'notify_on_plan_update']
    test_plan.emailing.notify_on_case_update = form.cleaned_data[
        'notify_on_case_update']
    test_plan.emailing.auto_to_plan_author = form.cleaned_data['auto_to_plan_author']
    test_plan.emailing.auto_to_case_owner = form.cleaned_data['auto_to_case_owner']
    test_plan.emailing.auto_to_case_default_tester = form.cleaned_data[
        'auto_to_case_default_tester']
    test_plan.emailing.save()


# _____________________________________________________________________________
# view functons

@method_decorator(permission_required('testplans.add_testplan'), name='dispatch')
class NewTestPlanView(View):
    template_name = 'testplans/mutable.html'

    def get(self, request):
        form = NewPlanForm()

        context_data = {
            'form': form
        }

        return render(request, self.template_name, context_data)

    def post(self, request):
        form = NewPlanForm(request.POST)
        form.populate(product_id=request.POST.get('product'))

        if form.is_valid():
            test_plan = TestPlan.objects.create(
                product=form.cleaned_data['product'],
                author=request.user,
                product_version=form.cleaned_data['product_version'],
                type=form.cleaned_data['type'],
                name=form.cleaned_data['name'],
                create_date=timezone.now(),
                extra_link=form.cleaned_data['extra_link'],
                parent=form.cleaned_data['parent'],
                text=form.cleaned_data['text'],
                is_active=form.cleaned_data['is_active'],
            )

            update_plan_email_settings(test_plan, form)

            return HttpResponseRedirect(
                reverse('test_plan_url_short', args=[test_plan.pk, ])
            )

        context_data = {
            'form': form,
        }
        return render(request, self.template_name, context_data)


class SearchTestPlanView(TemplateView):  # pylint: disable=missing-permission-required

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

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    """
    query_set = TestCasePlan.objects.filter(plan__in=plan_ids).values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')

    number_of_plan_cases = {}
    for item in query_set:
        number_of_plan_cases[item['plan']] = item['total_count']

    return number_of_plan_cases


def get_number_of_plans_runs(plan_ids):
    """Get the number of runs related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    """
    query_set = TestRun.objects.filter(plan__in=plan_ids).values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    number_of_plan_runs = {}
    for item in query_set:
        number_of_plan_runs[item['plan']] = item['total_count']

    return number_of_plan_runs


def get_number_of_children_plans(plan_ids):
    """Get the number of children plans related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    """
    query_set = TestPlan.objects.filter(parent__in=plan_ids).values('parent').annotate(
        total_count=Count('parent')).order_by('-parent')
    number_of_children_plans = {}
    for item in query_set:
        number_of_children_plans[item['parent']] = item['total_count']

    return number_of_children_plans


def calculate_stats_for_testplans(plans):
    """Attach the number of cases and runs for each TestPlan

    Arguments:
    - plans: the queryset of TestPlans

    Return value:
    A list of TestPlans, each of which is attached the statistics which is
    with prefix cal meaning calculation result.
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


class TestPlanGetView(DetailView):  # pylint: disable=missing-permission-required

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
                        # todo: URL accepts POST, need to refactor to use GET+POST
                        # e.g. plans/3/clone/
                        reverse('plans-clone')
                    ),
                    (
                        _('History'),
                        "/admin/testplans/testplan/%d/history/" % self.object.pk
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
        # todo: this can be passed to the new template and consumed
        # in the JavaScript when rendering test cases based on status
        # confirmed_status = TestCaseStatus.get_confirmed()
        return context


class GetTestPlanRedirectView(DetailView):  # pylint: disable=missing-permission-required

    http_method_names = ['get']
    model = TestPlan

    def get(self, request, *args, **kwargs):
        test_plan = self.get_object()
        return HttpResponsePermanentRedirect(reverse('test_plan_url',
                                                     args=[test_plan.pk,
                                                           slugify(test_plan.name)]))


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.change_testplan')
def edit(request, pk):
    """Edit test plan view"""

    try:
        test_plan = TestPlan.objects.select_related().get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        form = NewPlanForm(request.POST)
        form.populate(product_id=request.POST.get('product'))

        # FIXME: Error handle
        if form.is_valid():
            test_plan.name = form.cleaned_data['name']
            test_plan.parent = form.cleaned_data['parent']
            test_plan.product = form.cleaned_data['product']
            test_plan.product_version = form.cleaned_data['product_version']
            test_plan.type = form.cleaned_data['type']
            test_plan.is_active = form.cleaned_data['is_active']
            test_plan.extra_link = form.cleaned_data['extra_link']
            test_plan.text = form.cleaned_data['text']
            test_plan.save()

            # Update plan email settings
            update_plan_email_settings(test_plan, form)
            return HttpResponseRedirect(
                reverse('test_plan_url', args=[pk, slugify(test_plan.name)]))
    else:
        form = NewPlanForm(initial={
            'name': test_plan.name,
            'product': test_plan.product_id,
            'product_version': test_plan.product_version_id,
            'type': test_plan.type_id,
            'text': test_plan.text,
            'parent': test_plan.parent_id,
            'is_active': test_plan.is_active,
            'extra_link': test_plan.extra_link,
            'auto_to_plan_author': test_plan.emailing.auto_to_plan_author,
            'auto_to_case_owner': test_plan.emailing.auto_to_case_owner,
            'auto_to_case_default_tester': test_plan.emailing.auto_to_case_default_tester,
            'notify_on_plan_update': test_plan.emailing.notify_on_plan_update,
            'notify_on_case_update': test_plan.emailing.notify_on_case_update,
        })
        form.populate(product_id=test_plan.product_id)

    context_data = {
        'test_plan': test_plan,
        'form': form,
    }
    return render(request, 'testplans/mutable.html', context_data)


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
