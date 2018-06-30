# -*- coding: utf-8 -*-

import datetime
from urllib.parse import urlencode

from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count
from django.db.models import Q
from django.contrib import messages
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404, HttpResponsePermanentRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.http import require_http_methods
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from uuslug import slugify

from tcms.core.models import TCMSLog
from tcms.core.utils import DataTableResult
from tcms.management.models import EnvGroup
from tcms.search import remove_from_request_path
from tcms.search.order import order_plan_queryset
from tcms.testcases.forms import SearchCaseForm, QuickSearchCaseForm
from tcms.testcases.models import TestCaseStatus
from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testcases.views import get_selected_testcases
from tcms.testcases.views import printable as testcases_printable
from tcms.testplans.forms import ClonePlanForm
from tcms.testplans.forms import EditPlanForm
from tcms.testplans.forms import NewPlanForm
from tcms.testplans.forms import SearchPlanForm
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun, TestCaseRun


def update_plan_email_settings(test_plan, form):
    """Update test plan's email settings"""
    test_plan.emailing.notify_on_plan_update = form.cleaned_data[
        'notify_on_plan_update']
    test_plan.emailing.notify_on_case_update = form.cleaned_data[
        'notify_on_case_update']
    test_plan.emailing.auto_to_plan_owner = form.cleaned_data['auto_to_plan_owner']
    test_plan.emailing.auto_to_plan_author = form.cleaned_data['auto_to_plan_author']
    test_plan.emailing.auto_to_case_owner = form.cleaned_data['auto_to_case_owner']
    test_plan.emailing.auto_to_case_default_tester = form.cleaned_data[
        'auto_to_case_default_tester']
    test_plan.emailing.save()


# _____________________________________________________________________________
# view functons


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.add_testplan')
def new(request, template_name='plan/new.html'):
    """New testplan"""

    # If the form has been submitted...
    if request.method == 'POST':
        # A form bound to the POST data
        form = NewPlanForm(request.POST, request.FILES)
        form.populate(product_id=request.POST.get('product'))

        if form.is_valid():
            test_plan = TestPlan.objects.create(
                product=form.cleaned_data['product'],
                author=request.user,
                owner=request.user,
                product_version=form.cleaned_data['product_version'],
                type=form.cleaned_data['type'],
                name=form.cleaned_data['name'],
                create_date=datetime.datetime.now(),
                extra_link=form.cleaned_data['extra_link'],
                parent=form.cleaned_data['parent'],
            )

            # Add test plan text
            if request.user.has_perm('testplans.add_testplantext'):
                test_plan.add_text(request.user, form.cleaned_data['text'])

            # Add test plan environment groups
            if request.user.has_perm('testplans.add_envplanmap'):
                if request.POST.get('env_group'):
                    env_groups = EnvGroup.objects.filter(
                        id__in=request.POST.getlist('env_group')
                    )

                    for env_group in env_groups:
                        test_plan.add_env_group(env_group=env_group)

            # create emailing settings to avoid Issue #181 on MySQL
            test_plan.emailing.save()

            return HttpResponseRedirect(
                reverse('test_plan_url_short', args=[test_plan.plan_id, ])
            )
    else:
        form = NewPlanForm()

    context_data = {
        'form': form,
    }
    return render(request, template_name, context_data)


@require_GET
def get_all(request, template_name='plan/all.html'):
    """Display all testplans"""
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

            # We want to get the number of cases and runs, without doing
            # lots of per-test queries.
            #
            # Ideally we would get the case/run counts using m2m field tricks
            # in the ORM
            # Unfortunately, Django's select_related only works on ForeignKey
            # relationships, not on ManyToManyField attributes
            # See http://code.djangoproject.com/ticket/6432

            # SQLAlchemy can handle this kind of thing in several ways.
            # Unfortunately we're using Django

            # The cleanest way I can find to get it into one query is to
            # use QuerySet.extra()
            # See http://docs.djangoproject.com/en/dev/ref/models/querysets
            tps = tps.annotate(num_cases=Count('case', distinct=True),
                               num_runs=Count('run', distinct=True),
                               num_children=Count('child_set', distinct=True))
            tps = order_plan_queryset(tps, order_by, asc)
    else:
        # Set search active plans only by default
        search_form = SearchPlanForm(initial={'is_active': True})

    if request.GET.get('action') == 'clone_case':
        template_name = 'case/clone_select_plan.html'
        tps = tps.order_by('name')

    if request.GET.get('t') == 'ajax':
        results = []
        for obj in tps:
            dict_obj = model_to_dict(obj, fields=('name', 'parent', 'is_active'))

            for attr in ['pk', 'num_cases', 'num_cases', 'num_runs', 'num_children']:
                dict_obj[attr] = getattr(obj, attr)
            dict_obj['get_full_url'] = obj.get_full_url()

            results.append(dict_obj)
        return JsonResponse(results, safe=False)

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


@require_GET
def ajax_search(request, template_name='plan/common/json_plans.txt'):
    """Display all testplans"""
    # If it's not a search the page will be blank
    test_plans = TestPlan.objects.none()
    # if it's a search request the request will be full
    if request.GET:
        search_form = SearchPlanForm(request.GET)
        search_form.populate(product_id=request.GET.get('product'))

        if search_form.is_valid():
            # Detemine the query is the user's plans and change the sub
            # module value
            author = request.GET.get('author__email__startswith')
            if author and len(search_form.changed_data) == 1:
                if request.user.is_authenticated:
                    if author == request.user.username or author == request.user.email:
                        query = Q(author__email__startswith=author) | \
                            Q(owner__email__startswith=author)
                        test_plans = TestPlan.objects.filter(query).distinct()
            else:
                test_plans = TestPlan.list(search_form.cleaned_data)
                test_plans = test_plans.select_related('author', 'owner', 'type', 'product')

    # columnIndexNameMap is required for correct sorting behavior, 5 should
    # be product, but we use run.build.product
    column_names = [
        '',
        'plan_id',
        'name',
        'author__username',
        'owner__username',
        'product',
        'product_version',
        'type',
        'num_cases',
        'num_runs',
        ''
    ]
    return ajax_response(request, test_plans, column_names, template_name)


def ajax_response(request, queryset, column_names, template_name):
    """ JSON template for the ajax request for searching """
    data_table_result = DataTableResult(request.GET, queryset, column_names)

    data = data_table_result.get_response_data()
    data['querySet'] = calculate_stats_for_testplans(data['querySet'])

    # todo: prepare the JSON with the response, consider using :
    # from django.template.defaultfilters import escapejs
    json_result = render_to_string(
        template_name,
        data,
        request=request)
    return HttpResponse(json_result, content_type='application/json')


def get(request, plan_id, slug=None, template_name='plan/get.html'):
    """Display the plan details."""

    try:
        test_plan = TestPlan.objects.select_related().get(plan_id=plan_id)
        test_plan.latest_text = test_plan.latest_text()
    except ObjectDoesNotExist:
        raise Http404

    # redirect if has a cheated slug
    if slug != slugify(test_plan.name):
        return HttpResponsePermanentRedirect(test_plan.get_full_url())

    # Initial the case counter
    confirm_status_name = 'CONFIRMED'
    test_plan.run_case = test_plan.case.filter(case_status__name=confirm_status_name)
    test_plan.review_case = test_plan.case.exclude(case_status__name=confirm_status_name)

    context_data = {
        'test_plan': test_plan,
    }
    return render(request, template_name, context_data)


@require_http_methods(['GET', 'POST'])
@permission_required('testruns.change_testrun')
def choose_run(request, plan_id):
    """Choose one run to add cases"""

    if request.method == 'GET':
        try:
            test_plan = TestPlan.objects.get(pk=int(plan_id))
        except ObjectDoesNotExist:
            raise Http404

        test_runs = TestRun.objects.filter(plan=plan_id).values('pk',
                                                                'summary',
                                                                'build__name',
                                                                'manager__username')

        # Ready to write cases to test plan
        test_cases = get_selected_testcases(request).values('pk', 'summary',
                                                            'author__username',
                                                            'create_date',
                                                            'category__name',
                                                            'priority__value', )

        context_data = {
            'plan_id': plan_id,
            'plan': test_plan,
            'test_runs': test_runs.iterator(),
            'test_cases': test_cases.iterator(),
        }
        return render(request, 'plan/choose_testrun.html', context_data)

    # Add cases to runs
    if request.method == 'POST':
        chosen_test_run_ids = request.POST.getlist('testrun_ids')
        to_be_added_cases = TestCase.objects.filter(pk__in=request.POST.getlist('case_ids'))

        # Adding cases to runs by recursion
        cases_selected = 0
        for test_run_id in chosen_test_run_ids:
            test_run = get_object_or_404(TestRun, run_id=test_run_id)
            cases = TestCaseRun.objects.filter(run=test_run_id)
            existing_cases = cases.values_list('case', flat=True)

            for test_case in to_be_added_cases:
                # counter used as a flag that runs or cases were selected
                # in the form, regardless of whether or not they were actually added
                # used to produce an error message if user clicked the Update button
                # without selecting anything on the screen
                cases_selected += 1
                if test_case.case_id not in existing_cases:
                    test_run.add_case_run(case=test_case)

            estimated_time = 0
            for case in to_be_added_cases:
                estimated_time += case.estimated_time

            test_run.estimated_time = test_run.estimated_time + estimated_time
            test_run.save()

        if not cases_selected:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Select at least one TestRun and one TestCase'))

        return HttpResponseRedirect(reverse('test_plan_url_short', args=[plan_id]))


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.change_testplan')
def edit(request, plan_id, template_name='plan/edit.html'):
    """Edit test plan view"""

    try:
        test_plan = TestPlan.objects.select_related().get(plan_id=plan_id)
    except ObjectDoesNotExist:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        form = EditPlanForm(request.POST, request.FILES)
        form.populate(product_id=request.POST.get('product'))

        # FIXME: Error handle
        if form.is_valid():
            if request.user.has_perm('testplans.change_testplan'):
                test_plan.name = form.cleaned_data['name']
                test_plan.parent = form.cleaned_data['parent']
                test_plan.product = form.cleaned_data['product']
                test_plan.product_version = form.cleaned_data['product_version']
                test_plan.type = form.cleaned_data['type']
                test_plan.is_active = form.cleaned_data['is_active']
                test_plan.extra_link = form.cleaned_data['extra_link']
                test_plan.owner = form.cleaned_data['owner']
                # IMPORTANT! tp.current_user is an instance attribute,
                # added so that in post_save, current logged-in user info
                # can be accessed.
                # Instance attribute is usually not a desirable solution.
                test_plan.current_user = request.user
                test_plan.save()

            if request.user.has_perm('testplans.add_testplantext'):
                test_plan.add_text(request.user, form.cleaned_data['text'])

            if request.user.has_perm('testplans.change_envplanmap'):
                test_plan.clear_env_groups()

                if request.POST.get('env_group'):
                    env_groups = EnvGroup.objects.filter(
                        id__in=request.POST.getlist('env_group'))

                    for env_group in env_groups:
                        test_plan.add_env_group(env_group=env_group)
            # Update plan email settings
            update_plan_email_settings(test_plan, form)
            return HttpResponseRedirect(
                reverse('test_plan_url', args=[plan_id, slugify(test_plan.name)]))
    else:
        # Generate a blank form
        # Temporary use one environment group in this case
        if test_plan.env_group.all():
            for env_group in test_plan.env_group.all():
                env_group_id = env_group.id
                break
        else:
            env_group_id = None

        form = EditPlanForm(initial={
            'name': test_plan.name,
            'product': test_plan.product_id,
            'product_version': test_plan.product_version_id,
            'type': test_plan.type_id,
            'text': test_plan.latest_text() and test_plan.latest_text().plan_text or '',
            'parent': test_plan.parent_id,
            'env_group': env_group_id,
            'is_active': test_plan.is_active,
            'extra_link': test_plan.extra_link,
            'owner': test_plan.owner,
            'auto_to_plan_owner': test_plan.emailing.auto_to_plan_owner,
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
    return render(request, template_name, context_data)


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.add_testplan')
def clone(request, template_name='plan/clone.html'):
    """Clone testplan"""

    req_data = request.GET or request.POST
    if 'plan' not in req_data:
        messages.add_message(request,
                             messages.ERROR,
                             _('At least one TestPlan is required'))
        # redirect back where we came from
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    plan_ids = req_data.getlist('plan')
    test_plans = TestPlan.objects.filter(pk__in=plan_ids)

    if not test_plans:
        # note: if at least one of the specified plans is found
        # we're not going to show this message
        messages.add_message(request,
                             messages.ERROR,
                             _('TestPlan(s) "%s" do not exist') % plan_ids)
        # redirect back where we came from
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    # Clone the plan if the form is submitted
    if request.method == "POST":
        clone_form = ClonePlanForm(request.POST)
        clone_form.populate(product_id=request.POST.get('product_id'))

        if clone_form.is_valid():
            clone_options = clone_form.cleaned_data

            # Create new test plan.
            for test_plan in test_plans:

                new_name = clone_options['name'] if len(test_plans) == 1 else None

                clone_params = dict(
                    # Cloned plan properties
                    new_name=new_name,
                    product=clone_options['product'],
                    version=clone_options['product_version'],
                    set_parent=clone_options['set_parent'],

                    # Related data
                    copy_texts=clone_options['copy_texts'],
                    copy_environment_group=clone_options['copy_environment_group'],

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

                assign_me_as_copied_case_default_tester = \
                    clone_options['copy_testcases'] and \
                    not clone_options['keep_case_default_tester']
                if assign_me_as_copied_case_default_tester:
                    clone_params['new_case_default_tester'] = request.user

                assign_me_as_text_author = not clone_options['copy_texts']
                if assign_me_as_text_author:
                    clone_params['default_text_author'] = request.user

                cloned_plan = test_plan.clone(**clone_params)

            if len(test_plans) == 1:
                return HttpResponseRedirect(
                    reverse('test_plan_url_short', args=[cloned_plan.plan_id]))

            args = {
                'action': 'search',
                'product': clone_form.cleaned_data['product'].id,
                'product_version': clone_form.cleaned_data['product_version'].id,
            }
            url_args = urlencode(args)
            return HttpResponseRedirect(
                '{}?{}'.format(reverse('plans-all'), url_args))
    else:
        # Generate the default values for the form
        if len(test_plans) == 1:
            clone_form = ClonePlanForm(initial={
                'product': test_plans[0].product_id,
                'product_version': test_plans[0].product_version_id,
                'set_parent': True,
                'copy_texts': True,
                'copy_attachements': True,
                'copy_environment_group': True,
                'link_testcases': True,
                'copy_testcases': False,
                'maintain_case_orignal_author': True,
                'keep_case_default_tester': False,
                'name': test_plans[0].make_cloned_name(),
            })
            clone_form.populate(product_id=test_plans[0].product.id)
        else:
            clone_form = ClonePlanForm(initial={
                'set_parent': True,
                'copy_texts': True,
                'copy_attachements': True,
                'link_testcases': True,
                'copy_testcases': False,
                'maintain_case_orignal_author': True,
                'keep_case_default_tester': True,
            })

    context_data = {
        'testplans': test_plans,
        'clone_form': clone_form,
    }
    return render(request, template_name, context_data)


def attachment(request, plan_id, template_name='plan/attachment.html'):
    """Manage attached files"""

    test_plan = get_object_or_404(TestPlan, plan_id=plan_id)
    context_data = {
        'test_plan': test_plan,
        'limit': settings.FILE_UPLOAD_MAX_SIZE,
    }
    return render(request, template_name, context_data)


@require_GET
def text_history(request, plan_id):
    """View test plan text history"""

    test_plan = get_object_or_404(TestPlan, plan_id=int(plan_id))
    test_plan_texts = test_plan.text.select_related('author').only('plan',
                                                                   'create_date',
                                                                   'plan_text',
                                                                   'author__email')
    context_data = {
        'testplan': test_plan,
        'test_plan_texts': test_plan_texts,
        'selected_text_version': int(request.GET.get('id', 0)),
    }
    return render(request, 'plan/history.html', context_data)


class ReorderCasesView(View):
    """Reorder cases"""

    http_method_names = ['post']

    def post(self, request, plan_id):
        # Current we should rewrite all of cases belong to the plan.
        # Because the cases sortkey in database is chaos,
        # Most of them are None.

        if 'case' not in request.POST:
            return JsonResponse({
                'rc': 1,
                'response': 'At least one case is required to re-order.'
            })

        plan = get_object_or_404(TestPlan, pk=int(plan_id))

        case_ids = []
        for case_id in request.POST.getlist('case'):
            case_ids.append(int(case_id))

        cases = TestCase.objects.filter(pk__in=case_ids).only('pk')

        for case in cases:
            new_sort_key = (case_ids.index(case.pk) + 1) * 10
            TestCasePlan.objects.filter(
                plan=plan, case=case).update(sortkey=new_sort_key)

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
            'case_status_id': TestCaseStatus.get_CONFIRMED()
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

        # Log Action
        plan_log = TCMSLog(model=plan)
        for case in cases:
            plan_log.make(
                who=request.user,
                action='Remove case {} from plan {}'.format(case.pk, plan.pk))
            case.log_action(who=request.user,
                            action='Remove from plan {}'.format(plan.pk))
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
