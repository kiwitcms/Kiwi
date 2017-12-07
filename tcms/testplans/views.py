# -*- coding: utf-8 -*-

import datetime
import itertools
import six

from six.moves import urllib

from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.db.models import Q
from django.http import Http404, HttpResponsePermanentRedirect
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import get_template
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_http_methods
from django.views.generic import View
from uuslug import slugify

from tcms.core.db import SQLExecution
from tcms.core.models import TCMSLog
from tcms.core.responses import HttpJSONResponse
from tcms.core.utils.checksum import checksum
from tcms.core.utils import DataTableResult
from tcms.core.utils.raw_sql import RawSQL
from tcms.core.views import Prompt
from tcms.management.models import TCMSEnvGroup, Component
from tcms.search.views import remove_from_request_path
from tcms.search.order import order_plan_queryset
from tcms.testcases.forms import SearchCaseForm, QuickSearchCaseForm
from tcms.testcases.models import TestCaseStatus, TestCaseCategory
from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testcases.views import get_selected_testcases
from tcms.testplans.forms import ClonePlanForm
from tcms.testplans.forms import EditPlanForm
from tcms.testplans.forms import ImportCasesViaXMLForm
from tcms.testplans.forms import NewPlanForm
from tcms.testplans.forms import PlanComponentForm
from tcms.testplans.forms import SearchPlanForm
from tcms.testplans import sqls
from tcms.testplans.models import TestPlan, TestPlanComponent
from tcms.testruns.models import TestRun, TestCaseRun
from tcms.utils.dict_utils import create_group_by_dict as create_dict


MODULE_NAME = "testplans"


# _____________________________________________________________________________
# helper functons


def update_plan_email_settings(tp, form):
    """Update testplan's email settings"""
    tp.emailing.notify_on_plan_update = form.cleaned_data[
        'notify_on_plan_update']
    tp.emailing.notify_on_plan_delete = form.cleaned_data[
        'notify_on_plan_delete']
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
                return render(request, template_name, context=context_data)

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
            if request.user.has_perm('management.add_tcmsenvplanmap'):
                if request.POST.get('env_group'):
                    env_groups = TCMSEnvGroup.objects.filter(
                        id__in=request.POST.getlist('env_group')
                    )

                    for env_group in env_groups:
                        tp.add_env_group(env_group=env_group)

            return HttpResponseRedirect(
                reverse('plan-get', args=[tp.plan_id])
            )
    else:
        form = NewPlanForm()

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'form': form,
    }
    return render(request, template_name, context=context_data)


@require_GET
@permission_required('testplans.delete_testplan')
def delete(request, plan_id):
    """Delete testplan"""
    if request.GET.get('sure', 'no') == 'no':
        # TODO: rewrite the response
        return HttpResponse("\
            <script>if(confirm('Are you sure you want to delete this plan %s? \
            \\n \\n \
            Click OK to delete or cancel to come back')) { \
                window.location.href='%s?sure=yes' \
            } else { \
                history.go(-1) \
            };</script>" % (plan_id, reverse('plan-delete', args=[plan_id])))
    elif request.GET.get('sure') == 'yes':
        tp = get_object_or_404(TestPlan, plan_id=plan_id)

        try:
            tp.delete()
            return HttpResponse(
                "<script>window.location.href='%s'</script>" % reverse(
                    'tcms.testplans.views.all')
            )
        except Exception:
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='Delete failed.',
                next='javascript:window.history.go(-1)',
            ))
    else:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='Nothing yet.',
            next='javascript:window.history.go(-1)',
        ))


@require_GET
def all(request, template_name='plan/all.html'):
    """Display all testplans"""
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
    if list(request.GET.items()):
        search_form = SearchPlanForm(request.GET)
        if request.GET.get('product'):
            search_form.populate(product_id=request.GET['product'])
        else:
            search_form.populate()

        if search_form.is_valid():
            # Detemine the query is the user's plans and change the sub
            # module value
            author = request.GET.get('author')
            if author and request.user.is_authenticated():
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
        # I wish to use 'default' argument, as the same as in ModelForm
        # But it does not seem to work
        search_form = SearchPlanForm(initial={'is_active': True})

    if request.GET.get('action') == 'clone_case':
        template_name = 'case/clone_select_plan.html'
        tps = tps.order_by('name')

    if request.GET.get('t') == 'ajax':
        return HttpResponse(serializers.serialize(
            request.GET.get('f', 'json'),
            tps,
            extras=('num_cases', 'num_runs', 'num_children', 'get_url_path')
        ))

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
    return render(request, template_name, context=context_data)


def get_number_of_plans_cases(plan_ids):
    """Get the number of cases related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    """
    qs = TestCasePlan.objects.filter(plan__in=plan_ids)
    qs = qs.values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    return dict([(item['plan'], item['total_count']) for item in qs])


def get_number_of_plans_runs(plan_ids):
    """Get the number of runs related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    """
    qs = TestRun.objects.filter(plan__in=plan_ids)
    qs = qs.values('plan').annotate(
        total_count=Count('pk')).order_by('-plan')
    return dict([(item['plan'], item['total_count']) for item in qs])


def get_number_of_children_plans(plan_ids):
    """Get the number of children plans related to each plan

    Arguments:
    - plan_ids: a tuple or list of TestPlans' id

    Return value:
    Return value is an dict object, where key is plan_id and the value is the
    total count.
    """
    qs = TestPlan.objects.filter(parent__in=plan_ids)
    qs = qs.values('parent').annotate(
        total_count=Count('parent')).order_by('-parent')
    return dict([(item['parent'], item['total_count']) for item in qs])


def calculate_stats_for_testplans(plans):
    """Attach the number of cases and runs for each TestPlan

    Arguments:
    - plans: the queryset of TestPlans

    Return value:
    A list of TestPlans, each of which is attached the statistics which is
    with prefix cal meaning calculation result.
    """
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
    """Display all testplans"""
    # Define the default sub module

    # If it's not a search the page will be blank
    tps = TestPlan.objects.none()
    # if it's a search request the page will be fill
    if list(request.GET.items()):
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
                if request.user.is_authenticated():
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
    return ajax_response(request, tps, column_names,
                         'plan/common/json_plans.txt')


def ajax_response(request, queryset, column_names, template_name):
    """json template for the ajax request for searching"""
    dt = DataTableResult(request.GET, queryset, column_names)

    data = dt.get_response_data()
    data['querySet'] = calculate_stats_for_testplans(data['querySet'])

    # prepare the JSON with the response, consider using :
    # from django.template.defaultfilters import escapejs
    t = get_template(template_name)
    return HttpJSONResponse(t.render(data, request))


def get(request, plan_id, slug=None, template_name='plan/get.html'):
    """Display the plan details."""
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
        'xml_form': ImportCasesViaXMLForm(),
    }
    return render(request, template_name, context=context_data)


@require_http_methods(['GET', 'POST'])
@permission_required('testruns.change_testrun')
def choose_run(request, plan_id, template_name='plan/choose_testrun.html'):
    """Choose one run to add cases"""

    # Define the default sub module
    SUB_MODULE_NAME = 'runs'
    if request.method == 'GET':
        try:
            plan_id = int(plan_id)
            tp = TestPlan.objects.filter(pk=plan_id).defer('product_version')[0]
        except IndexError:
            raise Http404

        testruns = TestRun.objects.filter(plan=plan_id).values(
            'pk', 'summary', 'build__name', 'manager__username')

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
        return render(request, template_name, context=context_data)

    # Add cases to runs
    if request.method == 'POST':
        choosed_testrun_ids = request.POST.getlist('testrun_ids')
        to_be_added_cases = TestCase.objects.filter(pk__in=request.POST.getlist('case_ids'))

        # cases and runs are required in this process
        if not len(choosed_testrun_ids) or not len(to_be_added_cases):
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='At least one test run and one case is required to add cases to runs.',
                next=reverse('plan-get', args=[plan_id]),
            ))

        # Adding cases to runs by recursion
        for tr_id in choosed_testrun_ids:
            testrun = get_object_or_404(TestRun, run_id=tr_id)
            cases = TestCaseRun.objects.filter(run=tr_id)
            exist_cases_id = cases.values_list('case', flat=True)

            for testcase in to_be_added_cases:
                if testcase.case_id not in exist_cases_id:
                    testrun.add_case_run(case=testcase)

            estimated_time = six.moves.reduce(
                lambda x, y: x + y,
                [nc.estimated_time for nc in to_be_added_cases])
            testrun.estimated_time = testrun.estimated_time + estimated_time
            testrun.save()

        return HttpResponseRedirect(reverse('plan-get', args=[plan_id]))


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.change_testplan')
def edit(request, plan_id, template_name='plan/edit.html'):
    """Edit test plan view"""
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
                return render(request, template_name, context=context_data)

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

            if request.user.has_perm('management.change_tcmsenvplanmap'):
                tp.clear_env_groups()

                if request.POST.get('env_group'):
                    env_groups = TCMSEnvGroup.objects.filter(
                        id__in=request.POST.getlist('env_group'))

                    for env_group in env_groups:
                        tp.add_env_group(env_group=env_group)
            # Update plan email settings
            update_plan_email_settings(tp, form)
            return HttpResponseRedirect(
                reverse('plan-get', args=[plan_id, slugify(tp.name)]))
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
            'notify_on_plan_delete': tp.emailing.notify_on_plan_delete,
        })
        form.populate(product_id=tp.product_id)

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'form': form,
    }
    return render(request, template_name, context=context_data)


@require_http_methods(['GET', 'POST'])
@permission_required('testplans.add_testplan')
def clone(request, template_name='plan/clone.html'):
    """Clone testplan"""
    SUB_MODULE_NAME = 'plans'

    req_data = request.GET or request.POST
    if 'plan' not in req_data:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one plan is required by clone function.',
            next='javascript:window.history.go(-1)',
        ))

    tps = TestPlan.objects.filter(pk__in=req_data.getlist('plan'))

    if not tps:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='The plan you specify does not exist in database.',
            next='javascript:window.history.go(-1)',
        ))

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
                    copy_attachments=clone_options['copy_attachements'],
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
                    reverse('plan-get', args=[cloned_plan.plan_id]))
            else:
                args = {
                    'action': 'search',
                    'product': clone_form.cleaned_data['product'].id,
                    'product_version': clone_form.cleaned_data['product_version'].id,
                }
                url_args = urllib.parse.urlencode(args)
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
    return render(request, template_name, context=context_data)


def attachment(request, plan_id, template_name='plan/attachment.html'):
    """Manage attached files"""
    SUB_MODULE_NAME = 'plans'

    file_size_limit = settings.MAX_UPLOAD_SIZE
    limit_readable = int(file_size_limit) / 2 ** 20  # Mb

    tp = get_object_or_404(TestPlan, plan_id=plan_id)
    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'limit': file_size_limit,
        'limit_readable': str(limit_readable) + "Mb",
    }
    return render(request, template_name, context=context_data)


@require_GET
def text_history(request, plan_id, template_name='plan/history.html'):
    """View test plan text history"""
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
    return render(request, template_name, context=context_data)


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
        return HttpResponseRedirect(reverse('plan-get', args=[plan_id]))


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


class ImportCasesView(View):
    """Import cases to a plan"""

    @method_decorator(permission_required('testcases.add_testcaseplan'))
    def post(self, request, plan_id):
        plan = get_object_or_404(TestPlan.objects.only('pk'), pk=int(plan_id))

        # Process import case from XML action
        xml_form = ImportCasesViaXMLForm(request.POST, request.FILES)

        if xml_form.is_valid():
            i = 0
            for case in xml_form.cleaned_data['xml_file']:
                i += 1

                # Get the case category from the case and related to
                # the product of the plan
                try:
                    category = TestCaseCategory.objects.get(
                        product=plan.product, name=case['category_name'])
                except TestCaseCategory.DoesNotExist:
                    category = TestCaseCategory.objects.create(
                        product=plan.product, name=case['category_name'])

                # Start to create the objects
                tc = TestCase.objects.create(
                    is_automated=case['is_automated'],
                    script='',
                    arguments='',
                    summary=case['summary'],
                    requirement='',
                    alias='',
                    estimated_time=0,
                    case_status_id=case['case_status_id'],
                    category_id=category.id,
                    priority_id=case['priority_id'],
                    author_id=case['author_id'],
                    default_tester_id=case['default_tester_id'],
                    notes=case['notes'],
                )
                TestCasePlan.objects.create(plan=plan, case=tc, sortkey=i * 10)

                tc.add_text(case_text_version=1,
                            author=case['author'],
                            action=case['action'],
                            effect=case['effect'],
                            setup=case['setup'],
                            breakdown=case['breakdown'])

                # handle tags
                if case['tags']:
                    for tag in case['tags']:
                        tc.add_tag(tag=tag)

                tc.add_to_plan(plan=plan)

            return HttpResponseRedirect(
                reverse('plan-get', args=[plan_id]) + '#testcases')
        else:
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Alert,
                info=xml_form.errors,
                next=reverse('plan-get', args=[plan_id]) + '#testcases'
            ))


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


class PlanComponentsActionView(View):
    """Manage a plan's components"""

    template_name = 'plan/get_component.html'

    def get(self, request):
        if 'plan' not in request.GET:
            return HttpResponseBadRequest('Plan ID is not in request.')
        plans = TestPlan.objects.filter(pk=int(request.GET['plan']))
        if not plans:
            return Http404('Plan ID {} does not exist.'.format(
                ', '.join(plans)))

        action = request.GET.get('a', 'get_component_list').lower()

        if action == 'get_form':
            return self.get_manage_form(request, plans)
        elif action == 'get_component_list':
            return self.get_default_component_list(request, plans[0])
        elif action == 'add':
            return self.add(request, plans[0], self._get_components())
        elif action == 'remove':
            components = self._get_components()
            return self.remove_components_from_plan(request, plans[0], components)
        elif action == 'update':
            return self.update_components(request, plans[0])

    def _get_components(self):
        if 'component' not in self.request.GET:
            return HttpResponseBadRequest('Component ID is not in request.')
        component_ids = [
            int(id) for id in self.request.GET.getlist('component')]
        return Component.objects.filter(pk__in=component_ids)

    @method_decorator(permission_required('testplans.add_testplancomponent'))
    def add(self, request, plan, components):
        """Add components to given plans"""
        list(six.moves.map(plan.add_component, components))

    @method_decorator(permission_required('testplans.delete_testplancomponent'))
    def remove_components_from_plan(self, request, plan, components=None):
        """Remove existing components from plans

        :param plan: instance of TestPlan, from which to remove components
            from this plan.
        :param components: instances of Component, which will be removed.
        """
        if components is None:
            TestPlanComponent.objects.filter(plan=plan).delete()
        else:
            list(six.moves.map(plan.remove_component, components))

        return self.get_default_component_list(request, plan)

    def update_components(self, request, plan):
        self.remove_components_from_plan(request, plan)
        self.add(request, plan, self._get_components())
        return self.get_default_component_list(request, plan)

    def get_manage_form(self, request, plans):
        """Return form content in order to select components"""
        plan_comps = TestPlanComponent.objects.filter(plan__in=plans)

        form = PlanComponentForm(tps=plans, initial={
            'component': plan_comps.values_list('component_id', flat=True),
        })

        q_format = request.GET.get('format', 'p')
        html = getattr(form, 'as_' + q_format)

        return HttpResponse(html())

    def get_default_component_list(self, request, plan):
        return render(request, self.template_name, context={'test_plan': plan})


def tree_view(request):
    """Whole tree view for plans"""
    # FIXME:


@require_GET
def printable(request, template_name='plan/printable.html'):
    """Create the printable copy for plan"""
    plan_pks = request.GET.getlist('plan')

    if not plan_pks:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one target is required.'))

    tps = TestPlan.objects.filter(pk__in=plan_pks).only('pk', 'name')

    def plan_generator():
        repeat = len(plan_pks)
        params_sql = ','.join(itertools.repeat('%s', repeat))
        sql = sqls.TP_PRINTABLE_CASE_TEXTS % (params_sql, params_sql)
        result_set = SQLExecution(sql, plan_pks * 2)
        group_data = itertools.groupby(result_set.rows, lambda data: data['plan_id'])
        cases_dict = dict((key, list(values)) for key, values in group_data)
        for tp in tps:
            tp.result_set = cases_dict.get(tp.plan_id, None)
            yield tp

    context_data = {
        'test_plans': plan_generator(),
    }

    return render(request, template_name, context=context_data)


@require_GET
def export(request, template_name='plan/export.xml'):
    """Export the plan"""
    plan_pks = request.GET.getlist('plan')
    if not plan_pks:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one target is required.'))
    timestamp = datetime.datetime.now()
    timestamp_str = '%02i-%02i-%02i' % (timestamp.year, timestamp.month, timestamp.day)

    context_data = {
        'data_generator': generator_proxy(plan_pks),
    }

    response = render(request, template_name, context=context_data)
    response['Content-Disposition'] = 'attachment; filename=tcms-testcases-%s.xml' % timestamp_str
    return response


def generator_proxy(plan_pks):
    def key_func(data):
        return (data['plan_id'], data['case_id'])

    params_sql = ','.join(itertools.repeat('%s', len(plan_pks)))
    metas = SQLExecution(sqls.TP_EXPORT_ALL_CASES_META % params_sql,
                         plan_pks).rows
    compoment_dict = create_dict(
        sqls.TP_EXPORT_ALL_CASES_COMPONENTS % params_sql,
        plan_pks,
        key_func)
    tag_dict = create_dict(sqls.TP_EXPORT_ALL_CASE_TAGS % params_sql,
                           plan_pks,
                           key_func)

    sql = sqls.TP_EXPORT_ALL_CASE_TEXTS % (params_sql, params_sql)
    plan_text_dict = create_dict(sql, plan_pks * 2, key_func)

    for meta in metas:
        plan_id = meta['plan_id']
        case_id = meta['case_id']
        c_meta = compoment_dict.get((plan_id, case_id), None)
        if c_meta:
            meta['c_meta'] = c_meta

        tag = tag_dict.get((plan_id, case_id), None)
        if tag:
            meta['tag'] = tag

        plan_text = plan_text_dict.get((plan_id, case_id), None)
        if plan_text:
            meta['latest_text'] = plan_text

        yield meta
