# -*- coding: utf-8 -*-

import datetime
from urllib.parse import urlencode
from functools import reduce

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
from tcms.core.utils.checksum import checksum
from tcms.core.utils import DataTableResult
from tcms.core.utils.raw_sql import RawSQL
from tcms.core.views import Prompt
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


MODULE_NAME = "testplans"


# _____________________________________________________________________________
# helper functons


def update_plan_email_settings(tp, form):
    '''Update testplan's email settings'''
    tp.emailing.notify_on_plan_update = form.cleaned_data[
        'notify_on_plan_update']
    tp.emailing.notify_on_case_update = form.cleaned_data[
        'notify_on_case_update']
    tp.emailing.auto_to_plan_owner = form.cleaned_data['auto_to_plan_owner']
    tp.emailing.auto_to_plan_author = form.cleaned_data['auto_to_plan_author']
    tp.emailing.auto_to_case_owner = form.cleaned_data['auto_to_case_owner']
    tp.emailing.auto_to_case_default_tester = form.cleaned_data[
        'auto_to_case_default_tester']
    tp.emailing.save()


# _____________________________________________________________________________
# view functons


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.add_testplan')
def new(request, template_name='plan/new.html'):
    """New testplan"""

    SUB_MODULE_NAME = "new_plan"

    # If the form has been submitted...
    if request.method == 'POST':
        # A form bound to the POST data
        form = NewPlanForm(request.POST, request.FILES)
        form.populate(product_id=request.POST.get('product'))

        # Process the upload plan document
        if form.is_valid():
            if form.cleaned_data.get('upload_plan_text'):
                # Set the summary form field to the uploaded text
                form.data['text'] = form.cleaned_data['text']

                # Generate the form
                context_data = {
                    'module': MODULE_NAME,
                    'sub_module': SUB_MODULE_NAME,
                    'form': form,
                }
                return render(request, template_name, context_data)

        # Process the test plan submit to the form

        if form.is_valid():
            tp = TestPlan.objects.create(
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
                tp.add_text(author=request.user, plan_text=form.cleaned_data['text'])

            # Add test plan environment groups
            if request.user.has_perm('testplans.add_envplanmap'):
                if request.POST.get('env_group'):
                    env_groups = EnvGroup.objects.filter(
                        id__in=request.POST.getlist('env_group')
                    )

                    for env_group in env_groups:
                        tp.add_env_group(env_group=env_group)

            # create emailing settings to avoid Issue #181 on MySQL
            tp.emailing.save()

            return HttpResponseRedirect(
                reverse('test_plan_url_short', args=[tp.plan_id, ])
            )
    else:
        form = NewPlanForm()

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'form': form,
    }
    return render(request, template_name, context_data)


@require_GET
def all(request, template_name='plan/all.html'):
    '''Display all testplans'''
    # Define the default sub module
    SUB_MODULE_NAME = 'plans'
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
        if request.GET.get('product'):
            search_form.populate(product_id=request.GET['product'])
        else:
            search_form.populate()

        if search_form.is_valid():
            # Detemine the query is the user's plans and change the sub
            # module value
            author = request.GET.get('author')
            if author and request.user.is_authenticated:
                if author == request.user.username or author == request.user.email:
                    SUB_MODULE_NAME = "my_plans"

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
            tps = tps.extra(select={
                'num_cases': RawSQL.num_cases,
                'num_runs': RawSQL.num_runs,
                'num_children': RawSQL.num_plans,
            })
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
            dict_obj['get_url_path'] = obj.get_url_path()

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
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plans': tps,
        'query_result': query_result,
        'search_plan_form': search_form,
        'query_url': query_url,
        'query_url_page_type': query_url_page_type,
        'page_type': page_type
    }
    return render(request, template_name, context_data)


def get_number_of_plans_cases(plan_ids):
    '''Get the number of cases related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    '''
    qs = TestCasePlan.objects.filter(plan__in=plan_ids)
    qs = qs.values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    return dict([(item['plan'], item['total_count']) for item in qs])


def get_number_of_plans_runs(plan_ids):
    '''Get the number of runs related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    '''
    qs = TestRun.objects.filter(plan__in=plan_ids)
    qs = qs.values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    return dict([(item['plan'], item['total_count']) for item in qs])


def get_number_of_children_plans(plan_ids):
    '''Get the number of children plans related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    '''
    qs = TestPlan.objects.filter(parent__in=plan_ids)
    qs = qs.values('parent').annotate(
        total_count=Count('parent')).order_by('-parent')
    return dict([(item['parent'], item['total_count']) for item in qs])


def calculate_stats_for_testplans(plans):
    '''Attach the number of cases and runs for each TestPlan

    Arguments:
    - plans: the queryset of TestPlans

    Return value:
    A list of TestPlans, each of which is attached the statistics which is
    with prefix cal meaning calculation result.
    '''
    plan_ids = [plan.pk for plan in plans]
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
    '''Display all testplans'''
    # Define the default sub module

    # If it's not a search the page will be blank
    tps = TestPlan.objects.none()
    # if it's a search request the request will be full
    if request.GET:
        search_form = SearchPlanForm(request.GET)
        if request.GET.get('product'):
            search_form.populate(product_id=request.GET['product'])
        else:
            search_form.populate()
        if search_form.is_valid():
            # Detemine the query is the user's plans and change the sub
            # module value
            author = request.GET.get('author__email__startswith')
            if author and len(search_form.changed_data) == 1:
                if request.user.is_authenticated:
                    if author == request.user.username or author == request.user.email:
                        q = Q(author__email__startswith=author) | \
                            Q(owner__email__startswith=author)
                        tps = TestPlan.objects.filter(q).distinct()
            else:
                tps = TestPlan.list(search_form.cleaned_data)
                tps = tps.select_related('author', 'owner', 'type', 'product')

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
    return ajax_response(request, tps, column_names, template_name)


def ajax_response(request, queryset, column_names, template_name):
    """json template for the ajax request for searching"""
    dt = DataTableResult(request.GET, queryset, column_names)

    data = dt.get_response_data()
    data['querySet'] = calculate_stats_for_testplans(data['querySet'])

    # todo: prepare the JSON with the response, consider using :
    # from django.template.defaultfilters import escapejs
    json_result = render_to_string(
        template_name,
        data,
        request=request)
    return HttpResponse(json_result, content_type='application/json')


def get(request, plan_id, slug=None, template_name='plan/get.html'):
    '''Display the plan details.'''
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.select_related().get(plan_id=plan_id)
        tp.latest_text = tp.latest_text()
    except ObjectDoesNotExist:
        raise Http404

    # redirect if has a cheated slug
    if slug != slugify(tp.name):
        return HttpResponsePermanentRedirect(tp.get_absolute_url())

    # Initial the case counter
    confirm_status_name = 'CONFIRMED'
    tp.run_case = tp.case.filter(case_status__name=confirm_status_name)
    tp.review_case = tp.case.exclude(case_status__name=confirm_status_name)

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
    }
    return render(request, template_name, context_data)


@require_http_methods(['GET', 'POST'])
@permission_required('testruns.change_testrun')
def choose_run(request, plan_id, template_name='plan/choose_testrun.html'):
    '''Choose one run to add cases'''

    # Define the default sub module
    SUB_MODULE_NAME = 'runs'
    if request.method == 'GET':
        try:
            plan_id = int(plan_id)
            tp = TestPlan.objects.filter(pk=plan_id).defer('product_version')[0]
        except IndexError:
            raise Http404

        testruns = TestRun.objects.filter(plan=plan_id).values('pk',
                                                               'summary',
                                                               'build__name',
                                                               'manager__username')

        # Ready to write cases to test plan
        tcs = get_selected_testcases(request)
        tcs = tcs.values('pk', 'summary',
                         'author__username',
                         'create_date',
                         'category__name',
                         'priority__value', )

        context_data = {
            'module': MODULE_NAME,
            'sub_module': SUB_MODULE_NAME,
            'plan_id': plan_id,
            'plan': tp,
            'test_runs': testruns.iterator(),
            'test_cases': tcs.iterator(),
        }
        return render(request, template_name, context_data)

    # Add cases to runs
    if request.method == 'POST':
        chosen_testrun_ids = request.POST.getlist('testrun_ids')
        to_be_added_cases = TestCase.objects.filter(pk__in=request.POST.getlist('case_ids'))

        # Adding cases to runs by recursion
        cases_selected = 0
        for tr_id in chosen_testrun_ids:
            testrun = get_object_or_404(TestRun, run_id=tr_id)
            cases = TestCaseRun.objects.filter(run=tr_id)
            existing_cases = cases.values_list('case', flat=True)

            for testcase in to_be_added_cases:
                # counter used as a flag that runs or cases were selected
                # in the form, regardless of whether or not they were actually added
                # used to produce an error message if user clicked the Update button
                # without selecting anything on the screen
                cases_selected += 1
                if testcase.case_id not in existing_cases:
                    testrun.add_case_run(case=testcase)

            estimated_time = reduce(lambda x, y: x + y,
                                    [nc.estimated_time for nc in to_be_added_cases])
            testrun.estimated_time = testrun.estimated_time + estimated_time
            testrun.save()
        else:
            if not cases_selected:
                messages.add_message(request,
                                     messages.ERROR,
                                     _('Select at least one TestRun and one TestCase'))

        return HttpResponseRedirect(reverse('test_plan_url_short', args=[plan_id]))


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.change_testplan')
def edit(request, plan_id, template_name='plan/edit.html'):
    '''Edit test plan view'''
    # Define the default sub module
    SUB_MODULE_NAME = 'plans'

    try:
        tp = TestPlan.objects.select_related().get(plan_id=plan_id)
    except ObjectDoesNotExist:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        form = EditPlanForm(request.POST, request.FILES)
        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        else:
            form.populate()

        # FIXME: Error handle
        if form.is_valid():
            if form.cleaned_data.get('upload_plan_text'):
                # Set the summary form field to the uploaded text
                form.data['text'] = form.cleaned_data['text']

                # Generate the form
                context_data = {
                    'module': MODULE_NAME,
                    'sub_module': SUB_MODULE_NAME,
                    'form': form,
                    'test_plan': tp,
                }
                return render(template_name, context_data)

            if request.user.has_perm('testplans.change_testplan'):
                tp.name = form.cleaned_data['name']
                tp.parent = form.cleaned_data['parent']
                tp.product = form.cleaned_data['product']
                tp.product_version = form.cleaned_data['product_version']
                tp.type = form.cleaned_data['type']
                tp.is_active = form.cleaned_data['is_active']
                tp.extra_link = form.cleaned_data['extra_link']
                tp.owner = form.cleaned_data['owner']
                # IMPORTANT! tp.current_user is an instance attribute,
                # added so that in post_save, current logged-in user info
                # can be accessed.
                # Instance attribute is usually not a desirable solution.
                tp.current_user = request.user
                tp.save()

            if request.user.has_perm('testplans.add_testplantext'):
                new_text = request.POST.get('text')
                text_checksum = checksum(new_text)

                if not tp.text_exist() or text_checksum != tp.text_checksum():
                    tp.add_text(author=request.user,
                                plan_text=request.POST.get('text'),
                                text_checksum=text_checksum)

            if request.user.has_perm('testplans.change_envplanmap'):
                tp.clear_env_groups()

                if request.POST.get('env_group'):
                    env_groups = EnvGroup.objects.filter(
                        id__in=request.POST.getlist('env_group'))

                    for env_group in env_groups:
                        tp.add_env_group(env_group=env_group)
            # Update plan email settings
            update_plan_email_settings(tp, form)
            return HttpResponseRedirect(
                reverse('test_plan_url', args=[plan_id, slugify(tp.name)]))
    else:
        # Generate a blank form
        # Temporary use one environment group in this case
        if tp.env_group.all():
            for env_group in tp.env_group.all():
                env_group_id = env_group.id
                break
        else:
            env_group_id = None

        form = EditPlanForm(initial={
            'name': tp.name,
            'product': tp.product_id,
            'product_version': tp.product_version_id,
            'type': tp.type_id,
            'text': tp.latest_text() and tp.latest_text().plan_text or '',
            'parent': tp.parent_id,
            'env_group': env_group_id,
            'is_active': tp.is_active,
            'extra_link': tp.extra_link,
            'owner': tp.owner,
            'auto_to_plan_owner': tp.emailing.auto_to_plan_owner,
            'auto_to_plan_author': tp.emailing.auto_to_plan_author,
            'auto_to_case_owner': tp.emailing.auto_to_case_owner,
            'auto_to_case_default_tester': tp.emailing.auto_to_case_default_tester,
            'notify_on_plan_update': tp.emailing.notify_on_plan_update,
            'notify_on_case_update': tp.emailing.notify_on_case_update,
        })
        form.populate(product_id=tp.product_id)

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'form': form,
    }
    return render(request, template_name, context_data)


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.add_testplan')
def clone(request, template_name='plan/clone.html'):
    """Clone testplan"""
    SUB_MODULE_NAME = 'plans'

    req_data = request.GET or request.POST
    if 'plan' not in req_data:
        return Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one plan is required by clone function.',
            next='javascript:window.history.go(-1)',
        )

    tps = TestPlan.objects.filter(pk__in=req_data.getlist('plan'))

    if not tps:
        return Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='The plan you specify does not exist in database.',
            next='javascript:window.history.go(-1)',
        )

    # Clone the plan if the form is submitted
    if request.method == "POST":
        clone_form = ClonePlanForm(request.POST)
        clone_form.populate(product_id=request.POST.get('product_id'))

        if clone_form.is_valid():
            clone_options = clone_form.cleaned_data

            # Create new test plan.
            for tp in tps:

                new_name = len(tps) == 1 and clone_options['name'] or None

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

                cloned_plan = tp.clone(**clone_params)

            if len(tps) == 1:
                return HttpResponseRedirect(
                    reverse('test_plan_url_short', args=[cloned_plan.plan_id]))
            else:
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
        if len(tps) == 1:
            clone_form = ClonePlanForm(initial={
                'product': tps[0].product_id,
                'product_version': tps[0].product_version_id,
                'set_parent': True,
                'copy_texts': True,
                'copy_attachements': True,
                'copy_environment_group': True,
                'link_testcases': True,
                'copy_testcases': False,
                'maintain_case_orignal_author': True,
                'keep_case_default_tester': False,
                'name': tps[0].make_cloned_name(),
            })
            clone_form.populate(product_id=tps[0].product.id)
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
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplans': tps,
        'clone_form': clone_form,
    }
    return render(request, template_name, context_data)


def attachment(request, plan_id, template_name='plan/attachment.html'):
    '''Manage attached files'''
    SUB_MODULE_NAME = 'plans'

    tp = get_object_or_404(TestPlan, plan_id=plan_id)
    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'limit': settings.FILE_UPLOAD_MAX_SIZE,
    }
    return render(request, template_name, context_data)


@require_GET
def text_history(request, plan_id, template_name='plan/history.html'):
    '''View test plan text history'''
    SUB_MODULE_NAME = 'plans'

    tp = get_object_or_404(TestPlan, plan_id=int(plan_id))
    tptxts = tp.text.select_related('author').only('plan',
                                                   'create_date',
                                                   'plan_text',
                                                   'plan_text_version',
                                                   'author__email')
    selected_plan_text_version = int(request.GET.get('plan_text_version', 0))
    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplan': tp,
        'test_plan_texts': tptxts,
        'select_plan_text_version': selected_plan_text_version,
    }
    return render(request, template_name, context_data)


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

        case_ids = [int(id) for id in request.POST.getlist('case')]
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
        case_ids = [int(id) for id in request.POST.getlist('case')]
        cases = TestCase.objects.filter(case_id__in=case_ids).only('pk')
        for case in cases:
            plan.add_case(case)
        return HttpResponseRedirect(reverse('testplans-get', args=[plan_id]))


class LinkCasesSearchView(View):
    """Search cases for linking to plan"""

    template_name = 'plan/search_case.html'
    SUB_MODULE_NAME = 'plans'

    def get(self, request, plan_id):
        plan = get_object_or_404(TestPlan, pk=int(plan_id))

        normal_form = SearchCaseForm(initial={
            'product': plan.product_id,
            'product_version': plan.product_version_id,
            'case_status_id': TestCaseStatus.get_CONFIRMED()
        })
        quick_form = QuickSearchCaseForm()
        return render(self.request, self.template_name, {
            'module': MODULE_NAME,
            'sub_module': self.SUB_MODULE_NAME,
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
            'module': MODULE_NAME,
            'sub_module': self.SUB_MODULE_NAME,
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
    '''Create the printable copy for plan'''
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
