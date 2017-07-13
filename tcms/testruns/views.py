# -*- coding: utf-8 -*-

import datetime
import itertools
import json
import time
import urllib

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Count
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from django_comments.models import Comment

from tcms.core.exceptions import NitrateException
from tcms.core.responses import HttpJSONResponse
from tcms.core.utils import clean_request
from tcms.core.utils.raw_sql import RawSQL
from tcms.core.utils.tcms_router import connection
from tcms.core.utils.timedeltaformat import format_timedelta
from tcms.core.utils.validations import validate_bug_id
from tcms.core.views import Prompt
from tcms.management.models import Priority, TCMSEnvValue, TestTag
from tcms.search.forms import RunForm
from tcms.search.query import SmartDjangoQuery
from tcms.testcases.forms import CaseBugForm
from tcms.testcases.models import TestCasePlan, TestCaseStatus, TestCaseBugSystem
from tcms.testcases.views import get_selected_testcases
from tcms.testplans.models import TestPlan
from tcms.testruns.data import get_run_bug_ids
from tcms.testruns.data import stats_caseruns_status
from tcms.testruns.data import TestCaseRunDataMixin
from tcms.testruns.forms import MulitpleRunsCloneForm, PlanFilterRunForm
from tcms.testruns.forms import NewRunForm, SearchRunForm, EditRunForm, RunCloneForm
from tcms.testruns.helpers.serializer import TCR2File
from tcms.testruns.models import TestRun, TestCaseRun, TestCaseRunStatus, TCMSEnvRunValueMap
from tcms.issuetracker.types import IssueTrackerType


MODULE_NAME = "testruns"


@require_POST
@permission_required('testruns.add_testrun')
def new(request, template_name='run/new.html'):
    """Display the create test run page."""

    SUB_MODULE_NAME = "new_run"

    # If from_plan does not exist will redirect to plans for select a plan
    if not request.POST.get('from_plan'):
        return HttpResponseRedirect(reverse('plans-all'))

    plan_id = request.POST.get('from_plan')
    # Case is required by a test run
    if not request.POST.get('case'):
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one case is required by a run.',
            next=reverse('test_plan_url_short', args=[plan_id, ]),
        ))

    # Ready to write cases to test plan
    confirm_status = TestCaseStatus.get_CONFIRMED()
    tcs = get_selected_testcases(request)
    # FIXME: optimize this query, only get necessary columns, not all fields
    # are necessary
    tp = TestPlan.objects.select_related().get(plan_id=plan_id)
    tcrs = TestCaseRun.objects.filter(
        case_run_id__in=request.POST.getlist('case_run_id'))

    num_unconfirmed_cases = tcs.exclude(case_status=confirm_status).count()
    estimated_time = datetime.timedelta(seconds=0)

    tcs_values = tcs.select_related('author',
                                    'case_status',
                                    'category',
                                    'priority')
    # note: ordered for test_show_create_new_run_page() on PostgreSQL
    tcs_values = tcs_values.only('case_id',
                                 'summary',
                                 'estimated_time',
                                 'author__email',
                                 'create_date',
                                 'category__name',
                                 'priority__value',
                                 'case_status__name').order_by('case_id')

    if request.POST.get('POSTING_TO_CREATE'):
        form = NewRunForm(request.POST)
        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        else:
            form.populate(product_id=tp.product_id)

        if form.is_valid():
            # Process the data in form.cleaned_data
            default_tester = form.cleaned_data['default_tester']

            tr = TestRun.objects.create(
                product_version=form.cleaned_data['product_version'],
                plan_text_version=tp.latest_text() and tp.latest_text().plan_text_version or 0,
                stop_date=None,
                summary=form.cleaned_data.get('summary'),
                notes=form.cleaned_data.get('notes'),
                plan=tp,
                build=form.cleaned_data['build'],
                manager=form.cleaned_data['manager'],
                default_tester=default_tester,
                estimated_time=form.cleaned_data['estimated_time'],
                auto_update_run_status=form.cleaned_data['auto_update_run_status']
            )

            keep_status = form.cleaned_data['keep_status']
            keep_assign = form.cleaned_data['keep_assignee']

            try:
                assignee_tester = User.objects.get(username=default_tester)
            except ObjectDoesNotExist:
                assignee_tester = None

            loop = 1

            # not reserve assignee and status, assignee will default set to
            # default_tester
            if not keep_assign and not keep_status:
                for case in form.cleaned_data['case']:
                    try:
                        tcp = TestCasePlan.objects.get(plan=tp, case=case)
                        sortkey = tcp.sortkey
                    except ObjectDoesNotExist:
                        sortkey = loop * 10

                    tr.add_case_run(case=case,
                                    sortkey=sortkey,
                                    assignee=assignee_tester)
                    loop += 1

            # Add case to the run
            for tcr in tcrs:
                if (keep_status and keep_assign):
                    tr.add_case_run(case=tcr.case,
                                    assignee=tcr.assignee,
                                    case_run_status=tcr.case_run_status,
                                    sortkey=tcr.sortkey or loop * 10)
                    loop += 1
                elif keep_status and not keep_assign:
                    tr.add_case_run(case=tcr.case,
                                    case_run_status=tcr.case_run_status,
                                    sortkey=tcr.sortkey or loop * 10)
                    loop += 1
                elif keep_assign and not keep_status:
                    tr.add_case_run(case=tcr.case,
                                    assignee=tcr.assignee,
                                    sortkey=tcr.sortkey or loop * 10)
                    loop += 1

            # Write the values into tcms_env_run_value_map table
            env_property_id_set = set(request.POST.getlist("env_property_id"))
            if env_property_id_set:
                args = list()
                for property_id in env_property_id_set:
                    checkbox_name = 'select_property_id_%s' % property_id
                    select_name = 'select_property_value_%s' % property_id
                    checked = request.POST.getlist(checkbox_name)
                    if checked:
                        env_values = request.POST.getlist(select_name)
                        if not env_values:
                            continue

                        if len(env_values) != len(checked):
                            raise ValueError('Invalid number of env values.')

                        for value_id in env_values:
                            args.append(TCMSEnvRunValueMap(run=tr, value_id=value_id))

                TCMSEnvRunValueMap.objects.bulk_create(args)

            return HttpResponseRedirect(
                reverse('testruns-get', args=[tr.run_id, ])
            )

    else:
        estimated_time = reduce(lambda x, y: x + y,
                                (tc.estimated_time for tc in tcs_values))
        form = NewRunForm(initial={
            'summary': 'Test run for %s on %s' % (
                tp.name,
                tp.env_group.all() and tp.env_group.all()[0] or 'Unknown environment'
            ),
            'estimated_time': format_timedelta(estimated_time),
            'manager': tp.author.email,
            'default_tester': request.user.email,
            'product': tp.product_id,
            'product_version': tp.product_version_id,
        })
        form.populate(product_id=tp.product_id)

    # FIXME: pagination cases within Create New Run page.
    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'from_plan': plan_id,
        'test_plan': tp,
        'test_cases': tcs_values,
        'form': form,
        'num_unconfirmed_cases': num_unconfirmed_cases,
        'run_estimated_time': estimated_time,
    }
    return render(request, template_name, context_data)


@permission_required('testruns.delete_testrun')
def delete(request, run_id):
    '''Delete the test run

    - Maybe will be not use again

    '''
    try:
        tr = TestRun.objects.select_related('manager', 'plan').get(
            run_id=run_id
        )
    except ObjectDoesNotExist:
        raise Http404

    if not tr.belong_to(request.user):
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info="Permission denied - The run is not belong to you.",
            next='javascript:window.history.go(-1)'
        ))

    if request.GET.get('sure', 'no') == 'no':
        return HttpResponse("<script>\n \
            if(confirm('Are you sure you want to delete this run %s? \
            \\n \\n \
            Click OK to delete or cancel to come back')) \
            { window.location.href='/run/%s/delete/?sure=yes' } \
            else { history.go(-1) };</script>" % (run_id, run_id))
    elif request.GET.get('sure') == 'yes':
        try:
            plan_id = tr.plan_id
            tr.env_value.clear()
            tr.case_run.all().delete()
            tr.delete()
            return HttpResponseRedirect(
                reverse('test_plan_url_short', args=(plan_id, ))
            )
        except:
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info="Delete failed.",
                next='javascript:window.history.go(-1)'
            ))
    else:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info="Nothing yet",
            next='javascript:window.history.go(-1)'
        ))


@require_GET
def all(request, template_name='run/all.html'):
    '''Read the test runs from database and display them.'''
    SUB_MODULE_NAME = "runs"

    query_result = len(request.GET) > 0

    if request.GET.items():
        search_form = SearchRunForm(request.GET)
        if request.GET.get('product'):
            search_form.populate(product_id=request.GET['product'])
        else:
            search_form.populate()

        search_form.is_valid()
    else:
        search_form = SearchRunForm()

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'query_result': query_result,
        'search_form': search_form,
    }
    return render(request, template_name, context_data)


def run_queryset_from_querystring(querystring):
    '''Setup a run queryset from a querystring.

    A querystring is used in several places in front-end
    to query a list of runs.
    '''
    # 'name=alice&age=20' => {'name': 'alice', 'age': ''}
    filter_keywords = dict(k.split('=') for k in querystring.split('&'))
    # get rid of empty values and several other noisy names
    if "page_num" in filter_keywords:
        filter_keywords.pop('page_num')
    if "page_size" in filter_keywords:
        filter_keywords.pop('page_size')

    filter_keywords = dict(
        (str(k), v) for (k, v) in filter_keywords.iteritems() if v.strip())

    trs = TestRun.objects.filter(**filter_keywords)
    return trs


def magic_convert(queryset, key_name, value_name):
    return dict(((row[key_name], row[value_name]) for row in queryset))


@require_GET
def load_runs_of_one_plan(request, plan_id,
                          template_name='plan/common/json_plan_runs.txt'):
    """A dedicated view to return a set of runs of a plan

    This view is used in a plan detail page, for the contained testrun tab. It
    replaces the original solution, with a paginated resultset in return,
    serves as a performance healing. Also, in order for user to locate the
    data, it accepts field lookup parameters collected from the filter panel
    in the UI.
    """
    column_index_name_map = {0: '',
                             1: 'run_id',
                             2: 'summary',
                             3: 'manager__username',
                             4: 'default_tester__username',
                             5: 'start_date',
                             6: 'build__name',
                             7: 'stop_date',
                             8: 'total_num_caseruns',
                             9: 'failure_caseruns_percent',
                             10: 'successful_caseruns_percent',
                             }

    tp = TestPlan.objects.get(plan_id=plan_id)
    form = PlanFilterRunForm(request.GET)

    if form.is_valid():
        queryset = tp.run.filter(**form.cleaned_data)
        queryset = queryset.select_related(
            'build', 'manager', 'default_tester').order_by('-pk')

        total_records = total_display_records = queryset.count()

        queryset = sort_queryset(request, queryset, column_index_name_map)
        queryset = datatable_paginate(request, queryset)

        # Get associated statistics data
        run_filters = dict(('run__{0}'.format(key), value)
                           for key, value in form.cleaned_data.iteritems())

        qs = TestCaseRun.objects \
            .filter(case_run_status=TestCaseRunStatus.id_failed(),
                    **run_filters) \
            .values('run', 'case_run_status') \
            .annotate(count=Count('pk')).order_by('run', 'case_run_status')
        failure_subtotal = magic_convert(qs,
                                         key_name='run', value_name='count')

        qs = TestCaseRun.objects \
            .filter(case_run_status=TestCaseRunStatus.id_passed(),
                    **run_filters) \
            .values('run', 'case_run_status') \
            .annotate(count=Count('pk')).order_by('run', 'case_run_status')
        success_subtotal = magic_convert(qs,
                                         key_name='run', value_name='count')

        qs = TestCaseRun.objects.filter(**run_filters).values('run') \
            .annotate(count=Count('case')).order_by('run')
        cases_subtotal = magic_convert(qs,
                                       key_name='run', value_name='count')

        for run in queryset:
            run_id = run.pk
            cases_count = cases_subtotal.get(run_id, 0)
            if cases_count:
                failure_percent = failure_subtotal.get(run_id, 0) * 1.0 / cases_count * 100
                success_percent = success_subtotal.get(run_id, 0) * 1.0 / cases_count * 100
            else:
                failure_percent = success_percent = 0
            run.nitrate_stats = {
                'cases': cases_count,
                'failure_percent': failure_percent,
                'success_percent': success_percent,
            }
    else:
        queryset = TestRun.objects.none()
        total_records = total_display_records = queryset.count()

    context = {
        'sEcho': int(request.GET.get('sEcho', 0)),
        'iTotalRecords': total_records,
        'iTotalDisplayRecords': total_display_records,
        'runs': queryset,
    }
    json_data = render_to_string(template_name, context, request=request)
    return HttpJSONResponse(json_data)


@require_GET
def ajax_search(request, template_name='run/common/json_runs.txt'):
    """Response request to search test runs from Search Runs"""
    column_index_name_map = {0: '',
                             1: 'run_id',
                             2: 'summary',
                             3: 'manager__username',
                             4: 'default_tester__username',
                             5: 'plan',
                             6: 'build__product__name',
                             7: 'product_version',
                             8: 'plan__env_group__name',
                             9: 'total_num_caseruns',
                             10: 'stop_date',
                             11: 'completed',
                             }

    search_form = SearchRunForm(request.GET)
    if request.GET.get('product'):
        search_form.populate(product_id=request.GET['product'])
    else:
        search_form.populate()

    if search_form.is_valid():
        trs = TestRun.list(search_form.cleaned_data)
        trs = trs.select_related(
            'manager',
            'default_tester',
            'build',
            'plan',
            'build').only('run_id',
                          'summary',
                          'manager__username',
                          'default_tester__id',
                          'default_tester__username',
                          'plan__name',
                          'plan__env_group__name',
                          'build__product__name',
                          'stop_date',
                          'product_version__value')

        # Further optimize by adding caserun attributes:
        total_records = total_display_records = trs.count()

        trs = sort_queryset(request, trs, column_index_name_map)
        trs = datatable_paginate(request, trs)

        # Get associated statistics data
        run_ids = [run.pk for run in trs]
        qs = TestCaseRun.objects \
            .filter(case_run_status=TestCaseRunStatus.id_failed(),
                    run__in=run_ids) \
            .values('run', 'case_run_status') \
            .annotate(count=Count('pk')) \
            .order_by('run', 'case_run_status')
        failure_subtotal = magic_convert(qs,
                                         key_name='run',
                                         value_name='count')

        completed_status_ids = TestCaseRunStatus._get_completed_status_ids()
        qs = TestCaseRun.objects \
            .filter(case_run_status__in=completed_status_ids,
                    run__in=run_ids) \
            .values('run', 'case_run_status') \
            .annotate(count=Count('pk')) \
            .order_by('run', 'case_run_status')
        completed_subtotal = dict((
            (run_id, sum((item['count'] for item in stats_rows)))
            for run_id, stats_rows
            in itertools.groupby(qs.iterator(),
                                 key=lambda row: row['run'])))

        qs = TestCaseRun.objects \
            .filter(run__in=run_ids) \
            .values('run') \
            .annotate(cases_count=Count('case'))
        cases_subtotal = magic_convert(qs,
                                       key_name='run',
                                       value_name='cases_count')

        env_groups = {}
        for grp in TestPlan.objects.filter(
                pk__in=[run.plan_id for run in trs]).prefetch_related(
                'env_group').values('pk', 'env_group__name'):
            env_groups[grp['pk']] = grp['env_group__name']

        for run in trs:
            run.env_groups = env_groups[run.plan_id]
            run_id = run.pk
            cases_count = cases_subtotal.get(run_id, 0)
            if cases_count:
                completed_percent = completed_subtotal.get(run_id, 0) * 1.0 / cases_count * 100
                failure_percent = failure_subtotal.get(run_id, 0) * 1.0 / cases_count * 100
            else:
                completed_percent = failure_percent = 0
            run.nitrate_stats = {
                'cases': cases_count,
                'completed_percent': completed_percent,
                'failure_percent': failure_percent,
            }
    else:
        trs = TestRun.objects.none()
        total_records = total_display_records = trs.count()

    # columnIndexNameMap is required for correct sorting behavior, 5 should
    # be product, but we use run.build.product
    context = {
        'sEcho': int(request.GET.get('sEcho', 0)),
        'iTotalRecords': total_records,
        'iTotalDisplayRecords': total_display_records,
        'runs': trs,
    }
    json_data = render_to_string(template_name, context, request=request)
    return HttpJSONResponse(json_data)


def datatable_paginate(request, queryset):
    """Paginate queryset

    DataTable sends request with pagination information that is extracted and
    used to paginate queried queryset.
    """
    # Safety measure. If someone messes with iDisplayLength manually,
    # we clip it to the max value of 100.
    display_length = int(request.GET.get('iDisplayLength', settings.DEFAULT_PAGE_SIZE))
    # Where the data starts from (page)
    start_record = int(request.GET.get('iDisplayStart', 0))
    # where the data ends (end of page)
    end_record = start_record + display_length

    return queryset[start_record:end_record]


def get_sorting_cols(request, index_column_name_mapping):
    """Find sorting column and sort direction for each of them

    This works on top of parameters passed along with HTTP request by
    DataTable.

    :param HTTPRequest request: request object containing sorting information
    passed by DataTable.
    :param dict index_column_name_mapping: a mapping from column index to
    column name. This is passed by a method that is calling this method.
    :return: sequence of column names sort on. Sort direction will be prefixed
    if desc is specified by DataTable. If there is no sorting columns found,
    an empty sequence is returned, that is safe to pass to QuerySet that will
    not cause Django to generate ORDER BY clause.
    :rtype: list
    """
    get = request.GET.get

    iSortingCols = int(get('iSortingCols', 0))
    if not iSortingCols:
        return []

    mapping = ((int(get('iSortCol_{0}'.format(sorting_col_index))),
                get('sSortDir_{0}'.format(sorting_col_index)))
               for sorting_col_index in range(0, iSortingCols)
               if get('bSortable_{0}'.format(
                   get('iSortCol_{0}'.format(sorting_col_index)))) == u'true')

    return ['{0}{1}'.format('-' if sSortDir_N == 'desc' else '',
                            index_column_name_mapping[iSortCol_N])
            for iSortCol_N, sSortDir_N in mapping]


def sort_queryset(request, queryset, index_column_name_mapping):
    """Sort queryset on specified column by DataTable

    Each time an AJAX request from DataTable to sort on a particular column,
    a set of variable are sent together within the HTTP request. All of them
    are used to determine which column queryset is sorted on, which columns are
    sortable (that is defined by JavaScript code in client side), which
    direction to sort the column that is ASC or DESC.

    :param dict index_column_name_mapping: a mapping from column index to
    column name, that is used to find and construct the sequence of columns to
    sort on and the sort direction. This mapping must be as same as the column
    definitions in client side.
    """
    sorting_cols = get_sorting_cols(request, index_column_name_mapping)
    return queryset.order_by(*sorting_cols)


def open_run_get_case_runs(request, run):
    '''Prepare for case runs list in a TestRun page

    This is an internal method. Do not call this directly.
    '''
    tcrs = run.case_run.select_related('run', 'case')
    tcrs = tcrs.only('run__run_id',
                     'run__plan',
                     'case_run_status',
                     'assignee', 'tested_by',
                     'case_text_version',
                     'sortkey',
                     'case__summary',
                     'case__is_automated_proposed',
                     'case__is_automated',
                     'case__priority',
                     'case__category__name')
    # Get the bug count for each case run
    # 5. have to show the number of bugs of each case run
    tcrs = tcrs.extra(select={
        'num_bug': RawSQL.num_case_run_bugs,
    })
    tcrs = tcrs.distinct()
    # Continue to search the case runs with conditions
    # 4. case runs preparing for render case runs table
    tcrs = tcrs.filter(**clean_request(request))
    order_by = request.GET.get('order_by')
    if order_by:
        tcrs = tcrs.order_by(order_by)
    else:
        tcrs = tcrs.order_by('sortkey', 'pk')
    return tcrs


def open_run_get_comments_subtotal(case_run_ids):
    ct = ContentType.objects.get_for_model(TestCaseRun)
    qs = Comment.objects.filter(content_type=ct,
                                site_id=settings.SITE_ID,
                                object_pk__in=case_run_ids,
                                is_removed=False)
    qs = qs.values('object_pk').annotate(comment_count=Count('pk'))
    qs = qs.order_by('object_pk').iterator()
    result = ((int(row['object_pk']), row['comment_count']) for row in qs)
    return dict(result)


def open_run_get_users(case_runs):
    tester_ids = set()
    assignee_ids = set()
    for case_run in case_runs:
        if case_run.tested_by_id:
            tester_ids.add(case_run.tested_by_id)
        if case_run.assignee_id:
            assignee_ids.add(case_run.assignee_id)
    testers = User.objects.filter(
        pk__in=tester_ids).values_list('pk', 'username')
    assignees = User.objects.filter(
        pk__in=assignee_ids).values_list('pk', 'username')
    return (dict(testers.iterator()), dict(assignees.iterator()))


@require_GET
def get(request, run_id, template_name='run/get.html'):
    """Display testrun's detail"""

    SUB_MODULE_NAME = "runs"

    # Get the test run
    try:
        # 1. get test run itself
        tr = TestRun.objects.select_related().get(run_id=run_id)
    except ObjectDoesNotExist:
        raise Http404

    # Get the test case runs belong to the run
    # 2. get test run's all case runs
    tcrs = open_run_get_case_runs(request, tr)

    case_run_statuss = TestCaseRunStatus.objects.only('pk', 'name')
    case_run_statuss = case_run_statuss.order_by('pk')

    # Count the status
    # 3. calculate number of case runs of each status
    status_stats_result = stats_caseruns_status(run_id, case_run_statuss)

    # Get the test case run bugs summary
    # 6. get the number of bugs of this run
    tcr_bugs_count = tr.get_bug_count()

    # Get tag list of testcases
    # 7. get tags
    # Get the list of testcases belong to the run
    tcs = [tcr.case_id for tcr in tcrs]
    ttags = TestTag.objects.filter(cases__in=tcs).values_list('name', flat=True)
    ttags = list(set(ttags.iterator()))
    ttags.sort()

    def walk_case_runs():
        """Walking case runs for helping rendering case runs table"""
        priorities = Priority.get_values()
        testers, assignees = open_run_get_users(tcrs)
        comments_subtotal = open_run_get_comments_subtotal(
            [cr.pk for cr in tcrs])
        case_run_status = TestCaseRunStatus.get_names()

        for case_run in tcrs:
            yield (case_run,
                   testers.get(case_run.tested_by_id, None),
                   assignees.get(case_run.assignee_id, None),
                   priorities.get(case_run.case.priority_id),
                   case_run_status[case_run.case_run_status_id],
                   comments_subtotal.get(case_run.pk, 0))

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_run': tr,
        'from_plan': request.GET.get('from_plan', False),
        'test_case_runs': walk_case_runs(),
        'test_case_runs_count': len(tcrs),
        'status_stats': status_stats_result,
        'test_case_run_bugs_count': tcr_bugs_count,
        'test_case_run_status': case_run_statuss,
        'priorities': Priority.objects.all(),
        'case_own_tags': ttags,
        'bug_trackers': TestCaseBugSystem.objects.all(),
    }
    return render(request, template_name, context_data)


@permission_required('testruns.change_testrun')
def edit(request, run_id, template_name='run/edit.html'):
    """Edit test plan view"""
    # Define the default sub module
    SUB_MODULE_NAME = 'runs'

    try:
        tr = TestRun.objects.select_related().get(run_id=run_id)
    except ObjectDoesNotExist:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        form = EditRunForm(request.POST)
        if request.POST.get('product'):
            form.populate(product_id=request.POST.get('product'))
        else:
            form.populate(product_id=tr.plan.product_id)

        # FIXME: Error handler
        if form.is_valid():
            # detect if auto_update_run_status field is changed by user when
            # edit testrun.
            auto_update_changed = False
            if tr.auto_update_run_status \
                    != form.cleaned_data['auto_update_run_status']:
                auto_update_changed = True

            # detect if finished field is changed by user when edit testrun.
            finish_field_changed = False
            if tr.stop_date and not form.cleaned_data['finished']:
                finish_field_changed = True
                is_finish = False
            elif not tr.stop_date and form.cleaned_data['finished']:
                finish_field_changed = True
                is_finish = True

            tr.summary = form.cleaned_data['summary']
            # Permission hack
            if tr.manager == request.user or tr.plan.author == request.user:
                tr.manager = form.cleaned_data['manager']
            tr.default_tester = form.cleaned_data['default_tester']
            tr.build = form.cleaned_data['build']
            tr.product_version = form.cleaned_data['product_version']
            tr.notes = form.cleaned_data['notes']
            tr.estimated_time = form.cleaned_data['estimated_time']
            tr.auto_update_run_status = form.cleaned_data[
                'auto_update_run_status']
            tr.save()
            if auto_update_changed:
                tr.update_completion_status(is_auto_updated=True)
            if finish_field_changed:
                tr.update_completion_status(is_auto_updated=False,
                                            is_finish=is_finish)
            return HttpResponseRedirect(
                reverse('testruns-get', args=[run_id, ])
            )
    else:
        # Generate a blank form
        form = EditRunForm(initial={
            'summary': tr.summary,
            'manager': tr.manager.email,
            'default_tester': (tr.default_tester and
                               tr.default_tester.email or None),
            'product': tr.build.product_id,
            'product_version': tr.product_version_id,
            'build': tr.build_id,
            'notes': tr.notes,
            'finished': tr.stop_date,
            'estimated_time': tr.clear_estimated_time,
            'auto_update_run_status': tr.auto_update_run_status,
        })
        form.populate(product_id=tr.build.product_id)

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_run': tr,
        'form': form,
    }
    return render(request, template_name, context_data)


@permission_required('testruns.change_testcaserun')
def execute(request, run_id, template_name='run/execute.html'):
    '''Execute test run'''
    return get(request, run_id, template_name)


class TestRunReportView(TemplateView, TestCaseRunDataMixin):
    '''Test Run report'''

    template_name = 'run/report.html'

    def get(self, request, run_id):
        self.run_id = run_id
        return super(TestRunReportView, self).get(request, run_id)

    def get_context_data(self, **kwargs):
        '''Generate report for specific TestRun

        There are four data source to generate this report.
        1. TestRun
        2. Test case runs included in the TestRun
        3. Comments associated with each test case run
        4. Statistics
        5. bugs
        '''
        run = TestRun.objects.select_related('manager', 'plan').get(
            pk=self.run_id)

        case_runs = TestCaseRun.objects.filter(run=run).select_related(
            'case_run_status', 'case', 'tested_by').only(
            'close_date',
            'case_run_status__name',
            'case__category__name',
            'case__summary', 'case__is_automated',
            'case__is_automated_proposed',
            'tested_by__username')
        mode_stats = self.stats_mode_caseruns(case_runs)
        summary_stats = self.get_summary_stats(case_runs)

        test_case_run_bugs = []
        bug_system_types = {}
        for bug in get_run_bug_ids(self.run_id):
            # format the bug URLs based on DB settings
            test_case_run_bugs.append((
                bug['bug_id'],
                bug['bug_system__url_reg_exp'] % bug['bug_id'],
            ))
            # find out all unique bug tracking systems which were used to record
            # bugs in this particular test run. we use this data for reporting
            if bug['bug_system'] not in bug_system_types:
                # store a tracker type object for producing the report URL
                tracker_class = IssueTrackerType.from_name(bug['bug_system__tracker_type'])
                bug_system = TestCaseBugSystem.objects.get(pk=bug['bug_system'])
                tracker = tracker_class(bug_system)
                bug_system_types[bug['bug_system']] = (tracker, [])

            # store the list of bugs as well
            bug_system_types[bug['bug_system']][1].append(bug['bug_id'])

        # list of URLs which opens all bugs reported to every different
        # issue tracker used in this test run
        report_urls = []
        for (it, ids) in bug_system_types.values():
            report_url = it.all_issues_link(ids)
            # if IT doesn't support this feature or report url is not configured
            # the above method will return None
            if report_url:
                report_urls.append((it.tracker.name, report_url))

        caserun_bugs = self.get_caseruns_bugs(run.pk)
        comments = self.get_caseruns_comments(run.pk)

        for case_run in case_runs:
            bugs = caserun_bugs.get(case_run.pk, ())
            case_run.bugs = bugs
            case_run.user_comments = comments.get(case_run.pk, [])

        context = super(TestRunReportView, self).get_context_data(**kwargs)
        context.update({
            'test_run': run,
            'test_case_runs': case_runs,
            'test_case_runs_count': len(case_runs),
            'test_case_run_bugs': test_case_run_bugs,
            'mode_stats': mode_stats,
            'summary_stats': summary_stats,
            'report_urls': report_urls,
        })

        return context


@require_GET
@permission_required('testruns.change_testrun')
def bug(request, case_run_id, template_name='run/execute_case_run.html'):
    """Process the bugs for case runs."""

    class CaseRunBugActions(object):
        __all__ = ['add', 'file', 'remove', 'render_form']

        def __init__(self, request, case_run, template_name):
            self.request = request
            self.case_run = case_run
            self.template_name = template_name
            self.default_ajax_response = {'rc': 0, 'response': 'ok'}

        def add(self):
            if not self.request.user.has_perm('testcases.add_testcasebug'):
                response = {'rc': 1, 'response': 'Permission denied'}
                return self.ajax_response(response=response)

            bug_id = request.GET.get('bug_id')
            bug_system_id = request.GET.get('bug_system_id')

            try:
                validate_bug_id(bug_id, bug_system_id)
            except NitrateException as e:
                return self.ajax_response({
                    'rc': 1,
                    'response': str(e)
                })

            bz_external_track = True if request.GET.get('bz_external_track',
                                                        False) else False

            try:
                tcr.add_bug(bug_id=bug_id,
                            bug_system_id=bug_system_id,
                            bz_external_track=bz_external_track)
            except Exception as e:
                msg = str(e) if str(e) else 'Failed to add bug %s' % bug_id
                return self.ajax_response({
                    'rc': 1,
                    'response': msg
                })

            self.default_ajax_response.update({
                'run_bug_count': self.get_run_bug_count(),
                'caserun_bugs_count': self.case_run.get_bugs_count(),
            })
            return self.ajax_response()

        def ajax_response(self, response=None):
            if not response:
                response = self.default_ajax_response
            return HttpJSONResponse(json.dumps(response))

        def file(self):
            bug_system_id = request.GET.get('bug_system_id')
            bug_system = TestCaseBugSystem.objects.get(pk=bug_system_id)

            if bug_system.base_url:
                tracker = IssueTrackerType.from_name(bug_system.tracker_type)(bug_system)
                url = tracker.report_issue_from_testcase(self.case_run)
                response = {'rc': 0, 'response': url}
            else:
                response = {'rc': 1, 'response': 'Enable reporting to this Issue Tracker by configuring its base_url!'}

            return self.ajax_response(response)

        def remove(self):
            if not self.request.user.has_perm('testcases.delete_testcasebug'):
                response = {'rc': 1, 'response': 'Permission denied'}
                return self.render(response=response)

            try:
                bug_id = self.request.GET.get('bug_id')
                run_id = self.request.GET.get('case_run')
                self.case_run.remove_bug(bug_id, run_id)
            except ObjectDoesNotExist, error:
                response = {'rc': 1, 'response': str(error)}
                return self.ajax_response(response=response)

            self.default_ajax_response[
                'run_bug_count'] = self.get_run_bug_count()
            return self.ajax_response()

        def render_form(self):
            form = CaseBugForm(initial={
                'case_run': self.case_run.case_run_id,
                'case': self.case_run.case_id,
            })
            if self.request.GET.get('type') == 'table':
                return HttpResponse(form.as_table())

            return HttpResponse(form.as_p())

        def get_run_bug_count(self):
            run = self.case_run.run
            return run.get_bug_count()

    try:
        tcr = TestCaseRun.objects.get(case_run_id=case_run_id)
    except ObjectDoesNotExist:
        raise Http404

    crba = CaseRunBugActions(request=request,
                             case_run=tcr,
                             template_name=template_name)

    if not request.GET.get('a') in crba.__all__:
        return crba.ajax_response(response={
            'rc': 1,
            'response': 'Unrecognizable actions'})

    func = getattr(crba, request.GET['a'])
    return func()


@require_POST
def new_run_with_caseruns(request, run_id, template_name='run/clone.html'):
    """Clone cases from filter caserun"""

    SUB_MODULE_NAME = "runs"
    tr = get_object_or_404(TestRun, run_id=run_id)

    if request.POST.get('case_run'):
        tcrs = tr.case_run.filter(pk__in=request.POST.getlist('case_run'))
    else:
        tcrs = []

    if not tcrs:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one case is required by a run',
            next=request.META.get('HTTP_REFERER', '/')))
    estimated_time = reduce(lambda x, y: x + y,
                            [tcr.case.estimated_time for tcr in tcrs])

    if not request.POST.get('submit'):
        form = RunCloneForm(initial={
            'summary': tr.summary,
            'notes': tr.notes, 'manager': tr.manager.email,
            'product': tr.plan.product_id,
            'product_version': tr.product_version_id,
            'build': tr.build_id,
            'default_tester':
                tr.default_tester_id and tr.default_tester.email or '',
            'estimated_time': format_timedelta(estimated_time),
            'use_newest_case_text': True,
        })

        form.populate(product_id=tr.plan.product_id)

        context_data = {
            'module': MODULE_NAME,
            'sub_module': SUB_MODULE_NAME,
            'clone_form': form,
            'test_run': tr,
            'cases_run': tcrs,
        }
        return render(request, template_name, context_data)


@require_http_methods(['GET', 'POST'])
def clone(request, template_name='run/clone.html'):
    """Clone test run to another build"""

    SUB_MODULE_NAME = "runs"

    trs = TestRun.objects.select_related()

    req_data = request.GET or request.POST

    filter_str = req_data.get('filter_str')
    if filter_str:
        trs = run_queryset_from_querystring(filter_str)
    else:
        trs = trs.filter(pk__in=req_data.getlist('run'))

    if not trs:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one run is required',
            next=request.META.get('HTTP_REFERER', '/')
        ))

    # Generate the clone run page for one run
    if trs.count() == 1 and not req_data.get('submit'):
        tr = trs[0]
        tcrs = tr.case_run.all()
        form = RunCloneForm(initial={
            'summary': tr.summary,
            'notes': tr.notes,
            'manager': tr.manager.email,
            'product': tr.plan.product_id,
            'product_version': tr.product_version_id,
            'build': tr.build_id,
            'default_tester':
                tr.default_tester_id and tr.default_tester.email or '',
            'use_newest_case_text': True,
        })
        form.populate(product_id=tr.plan.product_id)

        context_data = {
            'module': MODULE_NAME,
            'sub_module': SUB_MODULE_NAME,
            'clone_form': form,
            'test_run': tr,
            'cases_run': tcrs,
        }
        return render(request, template_name, context_data)

    # Process multiple runs clone page
    template_name = 'run/clone_multiple.html'

    if request.method == "POST":
        form = MulitpleRunsCloneForm(request.POST)
        form.populate(trs=trs, product_id=request.POST.get('product'))
        if form.is_valid():
            for tr in trs:
                n_tr = TestRun.objects.create(
                    product_version=form.cleaned_data['product_version'],
                    plan_text_version=tr.plan_text_version,
                    summary=tr.summary,
                    notes=tr.notes,
                    estimated_time=tr.estimated_time,
                    plan=tr.plan,
                    build=form.cleaned_data['build'],
                    manager=(form.cleaned_data['update_manager'] and
                             form.cleaned_data['manager'] or
                             tr.manager),
                    default_tester=(
                        form.cleaned_data['update_default_tester'] and
                        form.cleaned_data['default_tester'] or
                        tr.default_tester),
                )

                for tcr in tr.case_run.all():
                    if form.cleaned_data['update_case_text']:
                        text_versions = list(tcr.get_text_versions())
                        if text_versions:
                            case_text_version = text_versions[-1]
                        else:
                            case_text_version = tcr.case_text_version
                    else:
                        case_text_version = tcr.case_text_version

                    n_tr.add_case_run(
                        case=tcr.case,
                        assignee=tcr.assignee,
                        case_text_version=case_text_version,
                        build=form.cleaned_data['build'],
                        notes=tcr.notes,
                        sortkey=tcr.sortkey,
                    )

                for env_value in tr.env_value.all():
                    n_tr.add_env_value(env_value)

                if form.cleaned_data['clone_cc']:
                    for cc in tr.cc.all():
                        n_tr.add_cc(user=cc)

                if form.cleaned_data['clone_tag']:
                    for tag in tr.tag.all():
                        n_tr.add_tag(tag=tag)

            if len(trs) == 1:
                return HttpResponseRedirect(
                    reverse('testruns-get', args=[n_tr.pk])
                )

            params = {
                'product': form.cleaned_data['product'].pk,
                'product_version': form.cleaned_data['product_version'].pk,
                'build': form.cleaned_data['build'].pk}

            return HttpResponseRedirect('%s?%s' % (
                reverse('testruns-all'),
                urllib.urlencode(params, True)
            ))
    else:
        form = MulitpleRunsCloneForm(initial={
            'run': trs.values_list('pk', flat=True),
            'manager': request.user,
            'default_tester': request.user,
            'assignee': request.user,
            'update_manager': False,
            'update_default_tester': True,
            'update_assignee': True,
            'update_case_text': True,
            'clone_cc': True,
            'clone_tag': True, })
        form.populate(trs=trs)

    context_data = {
        'module': MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'clone_form': form,
    }
    return render(request, template_name, context_data)


@require_POST
def order_case(request, run_id):
    '''Resort case with new order'''
    # Current we should rewrite all of cases belong to the plan.
    # Because the cases sortkey in database is chaos,
    # Most of them are None.
    get_object_or_404(TestRun, run_id=run_id)

    if 'case_run' not in request.POST:
        return HttpResponse(Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one case is required by re-oder in run.',
            next=reverse('testruns-get', args=[run_id, ]),
        ))

    case_run_ids = request.POST.getlist('case_run')
    sql = 'UPDATE test_case_runs SET sortkey = %s WHERE test_case_runs.case_run_id = %s'
    # sort key begin with 10, end with length*10, step 10.
    # e.g.
    # case_run_ids = [10334, 10294, 10315, 10443]
    #                      |      |      |      |
    #          sort key -> 10     20     30     40
    # then zip case_run_ids and new_sort_keys to pairs
    # e.g.
    #    sort_key, case_run_id
    #         (10, 10334)
    #         (20, 10294)
    #         (30, 10315)
    #         (40, 10443)
    new_sort_keys = xrange(10, (len(case_run_ids) + 1) * 10, 10)
    key_id_pairs = itertools.izip(new_sort_keys, (int(pk) for pk in case_run_ids))
    with transaction.atomic():
        for key_id_pair in key_id_pairs:
            cursor = connection.writer_cursor
            cursor.execute(sql, key_id_pair)

    return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))


@permission_required('testruns.change_testrun')
def change_status(request, run_id):
    '''Change test run finished or running'''
    tr = get_object_or_404(TestRun, run_id=run_id)

    if request.GET.get('finished') == '1':
        tr.update_completion_status(is_auto_updated=False, is_finish=True)
    else:
        tr.update_completion_status(is_auto_updated=False, is_finish=False)

    return HttpResponseRedirect(
        reverse('testruns-get', args=[run_id, ])
    )


@require_POST
@permission_required('testruns.delete_testcaserun')
def remove_case_run(request, run_id):
    """Remove specific case run from the run"""

    # Ignore invalid case run ids
    case_run_ids = []
    for item in request.POST.getlist('case_run'):
        try:
            case_run_ids.append(int(item))
        except (ValueError, TypeError):
            pass

    # If no case run to remove, no further operation is required, just return
    # back to run page immediately.
    if not case_run_ids:
        return HttpResponseRedirect(reverse('testruns-get',
                                            args=[run_id, ]))

    run = get_object_or_404(TestRun.objects.only('pk'), pk=run_id)

    # Restrict to delete those case runs that belongs to run
    TestCaseRun.objects.filter(run_id=run.pk, pk__in=case_run_ids).delete()

    caseruns_exist = TestCaseRun.objects.filter(run_id=run.pk).exists()
    if caseruns_exist:
        redirect_to = 'testruns-get'
    else:
        redirect_to = 'add-cases-to-run'

    return HttpResponseRedirect(reverse(redirect_to, args=[run_id, ]))


class AddCasesToRunView(View):
    """Add cases to a TestRun"""

    permission = 'testruns.add_testcaserun'
    template_name = 'run/assign_case.html'

    @method_decorator(permission_required(permission))
    def dispatch(self, *args, **kwargs):
        return super(AddCasesToRunView, self).dispatch(*args, **kwargs)

    def post(self, request, run_id):
        # Selected cases' ids to add to run
        ncs_id = request.POST.getlist('case')
        if not ncs_id:
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='At least one case is required by a run.',
                next=reverse('add-cases-to-run', args=[run_id, ]),
            ))

        try:
            ncs_id = map(int, ncs_id)
        except (ValueError, TypeError):
            return HttpResponse(Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='At least one case id is invalid.',
                next=reverse('add-cases-to-run', args=[run_id, ]),
            ))

        try:
            qs = TestRun.objects.select_related('plan').only('plan__plan_id')
            tr = qs.get(run_id=run_id)
        except ObjectDoesNotExist:
            raise Http404

        etcrs_id = tr.case_run.values_list('case', flat=True)

        # avoid add cases that are already in current run with pk run_id
        ncs_id = set(ncs_id) - set(etcrs_id)

        tp = tr.plan
        tcs = tr.plan.case.filter(case_status__name='CONFIRMED')
        tcs = tcs.select_related('default_tester').only('default_tester__id',
                                                        'estimated_time')
        ncs = tcs.filter(case_id__in=ncs_id)

        estimated_time = reduce(lambda x, y: x + y,
                                (nc.estimated_time for nc in ncs))
        tr.estimated_time = tr.estimated_time + estimated_time
        tr.save(update_fields=['estimated_time'])

        if request.POST.get('_use_plan_sortkey'):
            case_pks = (case.pk for case in ncs)
            qs = TestCasePlan.objects.filter(
                plan=tp, case__in=case_pks).values('case', 'sortkey')
            sortkeys_in_plan = dict((row['case'], row['sortkey'])
                                    for row in qs.iterator())
            for nc in ncs:
                sortkey = sortkeys_in_plan.get(nc.pk, 0)
                tr.add_case_run(case=nc, sortkey=sortkey)
        else:
            for nc in ncs:
                tr.add_case_run(case=nc)

        return HttpResponseRedirect(reverse('testruns-get',
                                            args=[tr.run_id, ]))

    def get(self, request, run_id):
        # information about TestRun, used in the page header
        tr = TestRun.objects.select_related(
            'plan', 'manager', 'build'
        ).only(
            'plan', 'plan__name',
            'manager__email', 'build__name'
        ).get(run_id=run_id)

        # select all CONFIRMED cases from the TestPlan that is a parent
        # of this particular TestRun
        rows = TestCasePlan.objects.values(
            'case',
            'case__create_date', 'case__summary',
            'case__category__name',
            'case__priority__value',
            'case__author__username'
        ).filter(
            plan_id=tr.plan,
            case__case_status=TestCaseStatus.objects.filter(name='CONFIRMED').first().pk
        ).order_by('case')  # order b/c of PostgreSQL

        # also grab a list of all TestCase IDs which are already present in the
        # current TestRun so we can mark them as disabled and not allow them to
        # be selected
        etcrs_id = TestCaseRun.objects.filter(run=run_id).values_list('case', flat=True)

        data = {
            'test_run': tr,
            'confirmed_cases': rows,
            'confirmed_cases_count': rows.count(),
            'test_case_runs_count': len(etcrs_id),
            'exist_case_run_ids': etcrs_id,
        }

        return render(request, self.template_name, data)


@require_GET
def cc(request, run_id):
    """Add or remove cc from a test run"""

    tr = get_object_or_404(TestRun, run_id=run_id)
    do = request.GET.get('do')
    username_or_email = request.GET.get('user')
    context_data = {'test_run': tr, 'is_ajax': True}

    if do:
        if not username_or_email:
            context_data['message'] = 'User name or email is required by this operation'
        else:
            try:
                user = User.objects.get(
                    Q(username=username_or_email) |
                    Q(email=username_or_email)
                )
            except ObjectDoesNotExist:
                context_data['message'] = 'The user you typed does not exist in database'
            else:
                if do == 'add':
                    tr.add_cc(user=user)

                if do == 'remove':
                    tr.remove_cc(user=user)

    return render(request, 'run/get_cc.html', context_data)


@require_POST
def update_case_run_text(request, run_id):
    """Update the IDLE cases to newest text"""

    tr = get_object_or_404(TestRun, run_id=run_id)

    if request.POST.get('case_run'):
        tcrs = tr.case_run.filter(pk__in=request.POST.getlist('case_run'))
    else:
        tcrs = tr.case_run.all()

    tcrs = tcrs.filter(case_run_status__name='IDLE')

    count = 0
    updated_tcrs = ''
    for tcr in tcrs:
        lctv = tcr.latest_text().case_text_version
        if tcr.case_text_version != lctv:
            count += 1
            updated_tcrs += '<li>%s: %s -> %s</li>' % (
                tcr.case.summary, tcr.case_text_version, lctv
            )
            tcr.case_text_version = lctv
            tcr.save()

    info = '<p>%s case run(s) succeed to update, following is the list:</p>\
    <ul>%s</ul>' % (count, updated_tcrs)

    return HttpResponse(Prompt.render(
        request=request,
        info_type=Prompt.Info,
        info=info,
        next=reverse('testruns-get', args=[run_id, ]),
    ))


@require_GET
def export(request, run_id):
    timestamp_str = time.strftime('%Y-%m-%d')
    case_runs = request.GET.getlist('case_run')
    format = request.GET.get('format', 'csv')
    # Export selected case runs
    if case_runs:
        tcrs = TestCaseRun.objects.filter(case_run_id__in=case_runs)
    # Export all case runs
    else:
        tcrs = TestCaseRun.objects.filter(run=run_id)
    response = HttpResponse()
    writer = TCR2File(tcrs)
    if format == 'csv':
        writer.write_to_csv(response)
        response['Content-Disposition'] = \
            'attachment; filename=tcms-testcase-runs-%s.csv' % timestamp_str
    else:
        writer.write_to_xml(response)
        response['Content-Disposition'] = \
            'attachment; filename=tcms-testcase-runs-%s.xml' % timestamp_str

    return response


@require_GET
def env_value(request):
    """Run environment property edit function"""
    trs = TestRun.objects.filter(run_id__in=request.GET.getlist('run_id'))

    class RunEnvActions(object):
        def __init__(self, requet, trs):
            self.__all__ = ['add', 'remove', 'change']
            self.ajax_response = {'rc': 0, 'response': 'ok'}
            self.request = request
            self.trs = trs

        def has_no_perm(self, perm):
            if not self.request.user.has_perm('testruns.' + perm + '_tcmsenvrunvaluemap'):
                return {'rc': 1, 'response': 'Permission deined - %s' % perm}

            return False

        def get_env_value(self, env_value_id):
            return TCMSEnvValue.objects.get(id=env_value_id)

        def add(self):
            chk_perm = self.has_no_perm('add')

            if chk_perm:
                return HttpResponse(json.dumps(chk_perm))

            try:
                value = self.get_env_value(request.GET.get('env_value_id'))
                for tr in self.trs:
                    o, c = tr.add_env_value(env_value=value)

                    if not c:
                        self.ajax_response = {
                            'rc': 1,
                            'response': 'The value is exist for this run'
                        }
            except ObjectDoesNotExist as errors:
                self.ajax_response = {'rc': 1, 'response': errors}
            except:
                raise

            fragment = render(request, "run/get_environment.html",
                              {"test_run": self.trs[0], "is_ajax": True})
            self.ajax_response.update({"fragment": fragment.content})
            return HttpResponse(json.dumps(self.ajax_response))

        def remove(self):
            chk_perm = self.has_no_perm('delete')
            if chk_perm:
                return HttpResponse(json.dumps(chk_perm))

            try:
                for tr in self.trs:
                    tr.remove_env_value(env_value=self.get_env_value(
                        request.GET.get('env_value_id')
                    ))
            except:
                pass

            return HttpResponse(json.dumps(self.ajax_response))

        def change(self):
            chk_perm = self.has_no_perm('change')
            if chk_perm:
                return HttpResponse(json.dumps(chk_perm))

            try:
                for tr in self.trs:
                    tr.remove_env_value(env_value=self.get_env_value(
                        request.GET.get('old_env_value_id')
                    ))

                    tr.add_env_value(env_value=self.get_env_value(
                        request.GET.get('new_env_value_id')
                    ))
            except:
                raise

            return HttpResponse(json.dumps(self.ajax_response))

    run_env_actions = RunEnvActions(request, trs)

    if request.GET.get('a') not in run_env_actions.__all__:
        ajax_response = {'rc': 1, 'response': 'Unrecognizable actions'}
        return HttpResponse(json.dumps(ajax_response))

    func = getattr(run_env_actions, request.GET['a'])
    return func()


def caseruns(request, templ='report/caseruns.html'):
    '''View that search caseruns.'''
    queries = request.GET
    r_form = RunForm(queries)
    r_form.populate(queries)
    context = {}
    if r_form.is_valid():
        runs = SmartDjangoQuery(r_form.cleaned_data, TestRun.__name__)
        runs = runs.evaluate()
        caseruns = get_caseruns_of_runs(runs, queries)
        context['test_case_runs'] = caseruns
        context['runs'] = runs
    return render(request, templ, context)


def get_caseruns_of_runs(runs, kwargs=None):
    '''
    Filtering argument -
        priority
        tester
        plan tag
    '''

    if kwargs is None:
        kwargs = {}
    plan_tag = kwargs.get('plan_tag', None)
    if plan_tag:
        runs = runs.filter(plan__tag__name=plan_tag)
    caseruns = TestCaseRun.objects.filter(run__in=runs)
    priority = kwargs.get('priority', None)
    if priority:
        caseruns = caseruns.filter(case__priority__pk=priority)
    tester = kwargs.get('tester', None)
    if not tester:
        caseruns = caseruns.filter(tested_by=None)
    if tester:
        caseruns = caseruns.filter(tested_by__pk=tester)
    status = kwargs.get('status', None)
    if status:
        caseruns = caseruns.filter(case_run_status__name__iexact=status)
    return caseruns
