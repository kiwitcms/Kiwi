# -*- coding: utf-8 -*-

import datetime

from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.http import Http404, HttpResponsePermanentRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from uuslug import slugify

from tcms.search import remove_from_request_path
from tcms.search.order import order_plan_queryset
from tcms.testcases.forms import SearchCaseForm, QuickSearchCaseForm
from tcms.testcases.models import TestCaseStatus
from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testcases.views import get_selected_testcases
from tcms.testcases.views import printable as testcases_printable
from tcms.testplans.forms import ClonePlanForm
from tcms.testplans.forms import NewPlanForm
from tcms.testplans.forms import SearchPlanForm
from tcms.testplans.models import TestPlan, PlanType
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
                create_date=datetime.datetime.now(),
                extra_link=form.cleaned_data['extra_link'],
                parent=form.cleaned_data['parent'],
                text=form.cleaned_data['text'],
                is_active=form.cleaned_data['is_active'],
            )

            update_plan_email_settings(test_plan, form)

            return HttpResponseRedirect(
                reverse('test_plan_url_short', args=[test_plan.plan_id, ])
            )

        context_data = {
            'form': form,
        }
        return render(request, self.template_name, context_data)


@require_GET
def get_all(request):
    """Display all testplans"""
    # todo: this function can be replaced with the existing JSON-RPC search
    # TODO: this function now only performs a forward feature, no queries
    # need here. All of it will be removed in the future.
    # If it's not a search the page will be blank
    tps = TestPlan.objects.none()
    query_result = False
    order_by = request.GET.get('order_by', 'create_date')
    asc = bool(request.GET.get('asc', None))
    # if it's a search request the page will be fill
    if request.GET:
        search_form = SearchPlanForm(request.GET)
        search_form.populate(product_id=request.GET.get('product'))

        if search_form.is_valid():
            query_result = True
            # build a QuerySet:
            tps = TestPlan.list(search_form.cleaned_data)
            tps = tps.select_related('author', 'type', 'product')
            tps = order_plan_queryset(tps, order_by, asc)
    else:
        # Set search active plans only by default
        search_form = SearchPlanForm(initial={'is_active': True})

    # fixme: this view is scheduled for deletion
    # TestCase clone workflow must be redesigned so it uses
    # the TestPlan search page
    template_name = ''
    if request.GET.get('action') == 'clone_case':
        template_name = 'case/clone_select_plan.html'
        tps = tps.order_by('name')

    # used in tree preview & TestCase add plan
    # fixme: must be replaced by JSON RPC and the
    # JavaScript dialog that displays the preview
    # should be converted to Patternfly
    # todo: when this is done SearchPlanForm must contain only the
    # fields which are used in search.html
    if request.GET.get('t') == 'html':
        if request.GET.get('f') == 'preview':
            template_name = 'plan/preview.html'

    query_url = remove_from_request_path(request, 'order_by')
    if asc:
        query_url = remove_from_request_path(query_url, 'asc')
    else:
        query_url = '%s&asc=True' % query_url
    page_type = request.GET.get('page_type', 'pagination')
    query_url_page_type = remove_from_request_path(request, 'page_type')
    if query_url_page_type:
        query_url_page_type = remove_from_request_path(query_url_page_type, 'page')

    context_data = {
        'test_plans': tps,
        'query_result': query_result,
        'search_plan_form': search_form,
        'query_url': query_url,
        'query_url_page_type': query_url_page_type,
        'page_type': page_type
    }
    return render(request, template_name, context_data)


@require_GET
def search(request):
    form = SearchPlanForm(request.GET)
    form.populate(product_id=request.GET.get('product'))

    context_data = {
        'form': form,
        'plan_types': PlanType.objects.all().only('pk', 'name').order_by('name'),
    }
    return render(request, 'testplans/search.html', context_data)


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


def get(request, plan_id, slug=None, template_name='plan/get.html'):
    """Display the plan details."""

    try:
        test_plan = TestPlan.objects.select_related().get(plan_id=plan_id)
    except ObjectDoesNotExist:
        raise Http404

    if slug is None:
        return HttpResponsePermanentRedirect(reverse('test_plan_url',
                                                     args=[plan_id, slugify(test_plan.name)]))

    # Initial the case counter
    confirm_status_name = 'CONFIRMED'
    test_plan.run_case = test_plan.case.filter(case_status__name=confirm_status_name)
    test_plan.review_case = test_plan.case.exclude(case_status__name=confirm_status_name)

    context_data = {
        'test_plan': test_plan,
    }
    return render(request, template_name, context_data)


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.change_testplan')
def edit(request, plan_id):
    """Edit test plan view"""

    try:
        test_plan = TestPlan.objects.select_related().get(plan_id=plan_id)
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
                reverse('test_plan_url', args=[plan_id, slugify(test_plan.name)]))
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


@require_POST
@permission_required('testplans.add_testplan')
def clone(request):
    """Clone testplan"""

    if 'plan' not in request.POST:
        messages.add_message(request,
                             messages.ERROR,
                             _('TestPlan is required'))
        # redirect back where we came from
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    plan_id = request.POST.get('plan')
    test_plan = get_object_or_404(TestPlan, pk=int(plan_id))

    post_data = request.POST.copy()
    if not request.POST.get('name'):
        post_data['name'] = test_plan.make_cloned_name()

    clone_form = ClonePlanForm(post_data)
    clone_form.populate(product_id=request.POST.get('product_id'))

    # if required values are missing we are still going to show
    # the form below, otherwise clone & redirect
    if clone_form.is_valid():
        clone_options = clone_form.cleaned_data

        # Create new test plan.
        new_name = clone_options['name']

        clone_params = dict(
            # Cloned plan properties
            new_name=new_name,
            product=clone_options['product'],
            version=clone_options['product_version'],
            set_parent=clone_options['set_parent'],

            # Link or copy cases
            link_cases=clone_options['link_testcases'],
            copy_cases=clone_options['copy_testcases'],
            default_component_initial_owner=request.user,
        )

        assign_me_as_plan_author = not clone_options['keep_orignal_author']
        if assign_me_as_plan_author:
            clone_params['new_original_author'] = request.user

        assign_me_as_copied_case_author = \
            clone_options['copy_testcases'] and \
            not clone_options['maintain_case_orignal_author']
        if assign_me_as_copied_case_author:
            clone_params['new_case_author'] = request.user

        # pylint: disable=invalid-name
        assign_me_as_copied_case_default_tester = \
            clone_options['copy_testcases'] and \
            not clone_options['keep_case_default_tester']
        if assign_me_as_copied_case_default_tester:
            clone_params['new_case_default_tester'] = request.user

        cloned_plan = test_plan.clone(**clone_params)

        return HttpResponseRedirect(
            reverse('test_plan_url_short', args=[cloned_plan.plan_id]))

    # clone form wasn't valid
    context_data = {
        'test_plan': test_plan,
        'clone_form': clone_form,
    }
    return render(request, 'plan/clone.html', context_data)


def attachment(request, plan_id, template_name='plan/attachment.html'):
    """Manage attached files"""

    test_plan = get_object_or_404(TestPlan, plan_id=plan_id)
    context_data = {
        'test_plan': test_plan,
        'limit': settings.FILE_UPLOAD_MAX_SIZE,
    }
    return render(request, template_name, context_data)


class ReorderCasesView(View):
    """Reorder cases"""

    http_method_names = ['post']

    def post(self, request, plan_id):
        if 'case' not in request.POST:
            return JsonResponse({
                'rc': 1,
                'response': 'At least one case is required to re-order.'
            })

        case_ids = []
        for case_id in request.POST.getlist('case'):
            case_ids.append(int(case_id))

        cases = TestCasePlan.objects.filter(case_id__in=case_ids, plan=plan_id).only('case_id')

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


class LinkCasesView(View):
    """Link cases to plan"""

    @method_decorator(permission_required('testcases.add_testcaseplan'))
    def post(self, request, plan_id):
        plan = get_object_or_404(TestPlan.objects.only('pk'), pk=int(plan_id))

        case_ids = []
        for case_id in request.POST.getlist('case'):
            case_ids.append(int(case_id))

        cases = TestCase.objects.filter(case_id__in=case_ids).only('pk')
        for case in cases:
            plan.add_case(case)

        return HttpResponseRedirect(reverse('test_plan_url', args=[plan_id, slugify(plan.name)]))


class LinkCasesSearchView(View):
    """Search cases for linking to plan"""

    template_name = 'plan/search_case.html'

    def get(self, request, plan_id):
        plan = get_object_or_404(TestPlan, pk=int(plan_id))

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

    def post(self, request, plan_id):
        plan = get_object_or_404(TestPlan, pk=int(plan_id))

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
                case_id__in=plan.case.values_list('case_id', flat=True))

        context = {
            'test_plan': plan,
            'test_cases': cases,
            'search_form': normal_form,
            'quick_form': quick_form,
            'search_mode': search_mode
        }
        return render(request, self.template_name, context=context)


class DeleteCasesView(View):
    """Delete selected cases from plan"""

    def post(self, request, plan_id):
        plan = get_object_or_404(TestPlan.objects.only('pk'), pk=int(plan_id))

        if 'case' not in request.POST:
            return JsonResponse({
                'rc': 1,
                'response': 'At least one case is required to delete.'
            })

        cases = get_selected_testcases(request).only('pk')
        for case in cases:
            plan.delete_case(case=case)

        return JsonResponse({'rc': 0, 'response': 'ok'})


@require_POST
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
