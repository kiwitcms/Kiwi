# -*- coding: utf-8 -*-

import json
import datetime
from http import HTTPStatus
from functools import reduce

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count
from django.db.models import Q
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from django_comments.models import Comment

from tcms.core.utils import clean_request
from tcms.core.utils import DataTableResult
from tcms.core.utils.validations import validate_bug_id
from tcms.management.models import Priority, EnvValue, Tag
from tcms.search.forms import RunForm
from tcms.search.query import SmartDjangoQuery
from tcms.testcases.forms import CaseBugForm
from tcms.testcases.models import TestCasePlan, TestCaseStatus, BugSystem
from tcms.testcases.views import get_selected_testcases
from tcms.testplans.models import TestPlan
from tcms.testruns.data import get_run_bug_ids
from tcms.testruns.data import TestCaseRunDataMixin
from tcms.testruns.forms import PlanFilterRunForm
from tcms.testruns.forms import NewRunForm, SearchRunForm, EditRunForm, RunCloneForm
from tcms.testruns.models import TestRun, TestCaseRun, TestCaseRunStatus, EnvRunValueMap
from tcms.issuetracker.types import IssueTrackerType


@require_POST
@permission_required('testruns.add_testrun')
def new(request, template_name='run/new.html'):
    """Display the create test run page."""

    # If from_plan does not exist will redirect to plans for select a plan
    if not request.POST.get('from_plan'):
        return HttpResponseRedirect(reverse('plans-all'))

    plan_id = request.POST.get('from_plan')
    # case is required by a test run
    # NOTE: currently this is handled in JavaScript but in the TestRun creation
    # form cases can be deleted
    if not request.POST.get('case'):
        messages.add_message(request,
                             messages.ERROR,
                             _('Creating a TestRun requires at least one TestCase'))
        return HttpResponseRedirect(reverse('test_plan_url_short', args=[plan_id]))

    # Ready to write cases to test plan
    confirm_status = TestCaseStatus.get_CONFIRMED()
    test_cases = get_selected_testcases(request)
    # FIXME: optimize this query, only get necessary columns, not all fields
    # are necessary
    test_plan = TestPlan.objects.select_related().get(plan_id=plan_id)
    test_case_runs = TestCaseRun.objects.filter(
        case_run_id__in=request.POST.getlist('case_run_id'))

    num_unconfirmed_cases = test_cases.exclude(case_status=confirm_status).count()
    estimated_time = datetime.timedelta(seconds=0)

    tcs_values = test_cases.select_related('author',
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
        form.populate(product_id=request.POST.get('product', test_plan.product_id))

        if form.is_valid():
            # Process the data in form.cleaned_data
            default_tester = form.cleaned_data['default_tester']

            test_run = TestRun.objects.create(
                product_version=form.cleaned_data['product_version'],
                stop_date=None,
                summary=form.cleaned_data.get('summary'),
                notes=form.cleaned_data.get('notes'),
                plan=test_plan,
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
                        tcp = TestCasePlan.objects.get(plan=test_plan, case=case)
                        sortkey = tcp.sortkey
                    except ObjectDoesNotExist:
                        sortkey = loop * 10

                    test_run.add_case_run(case=case,
                                          sortkey=sortkey,
                                          assignee=assignee_tester)
                    loop += 1

            # Add case to the run
            for test_case_run in test_case_runs:
                if (keep_status and keep_assign):
                    test_run.add_case_run(case=test_case_run.case,
                                          assignee=test_case_run.assignee,
                                          case_run_status=test_case_run.case_run_status,
                                          sortkey=test_case_run.sortkey or loop * 10)
                    loop += 1
                elif keep_status and not keep_assign:
                    test_run.add_case_run(case=test_case_run.case,
                                          case_run_status=test_case_run.case_run_status,
                                          sortkey=test_case_run.sortkey or loop * 10)
                    loop += 1
                elif keep_assign and not keep_status:
                    test_run.add_case_run(case=test_case_run.case,
                                          assignee=test_case_run.assignee,
                                          sortkey=test_case_run.sortkey or loop * 10)
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
                            args.append(EnvRunValueMap(run=test_run, value_id=value_id))

                EnvRunValueMap.objects.bulk_create(args)

            return HttpResponseRedirect(
                reverse('testruns-get', args=[test_run.run_id, ])
            )

    else:
        estimated_time = reduce(lambda x, y: x + y,
                                (tc.estimated_time for tc in tcs_values))
        form = NewRunForm(initial={
            'summary': 'Test run for %s on %s' % (
                test_plan.name,
                test_plan.env_group.all() and test_plan.env_group.all()[0] or 'Unknown environment'
            ),
            'estimated_time': estimated_time,
            'manager': test_plan.author.email,
            'default_tester': request.user.email,
            'product': test_plan.product_id,
            'product_version': test_plan.product_version_id,
        })
        form.populate(product_id=test_plan.product_id)

    # FIXME: pagination cases within Create New Run page.
    context_data = {
        'from_plan': plan_id,
        'test_plan': test_plan,
        'test_cases': tcs_values,
        'form': form,
        'num_unconfirmed_cases': num_unconfirmed_cases,
        'run_estimated_time': estimated_time.total_seconds(),
    }
    return render(request, template_name, context_data)


@permission_required('testruns.delete_testrun')
def delete(request, run_id):
    """Delete the test run

    - Maybe will be not use again

    """
    try:
        test_run = TestRun.objects.select_related('manager', 'plan').get(run_id=run_id)
    except ObjectDoesNotExist:
        raise Http404

    # should not happen under normal circumstances but malicious user may try
    # to post to the delete URL with another ID
    if not test_run.belong_to(request.user):
        messages.add_message(request,
                             messages.ERROR,
                             _('Permission denied: TestRun does not belong to you'))
        return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))

    if request.GET.get('sure', 'no') == 'no':
        return HttpResponse("<script>\n \
            if(confirm('Are you sure you want to delete this run %s? \
            \\n \\n \
            Click OK to delete or cancel to come back')) \
            { window.location.href='/run/%s/delete/?sure=yes' } \
            else { history.go(-1) };</script>" % (run_id, run_id))
    elif request.GET.get('sure') == 'yes':
        try:
            plan_id = test_run.plan_id
            test_run.env_value.clear()
            test_run.case_run.all().delete()
            test_run.delete()
            return HttpResponseRedirect(reverse('test_plan_url_short', args=(plan_id, )))
        except Exception as error:
            messages.add_message(request,
                                 messages.WARNING,
                                 _('Deletion failed: %s') % error)
            return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))
    else:
        messages.add_message(request,
                             messages.ERROR,
                             _('Parameter "sure" must be "yes" or "no"'))
        return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))


@require_GET
def get_all(request):
    """Read the test runs from database and display them."""
    query_result = len(request.GET) > 0

    if request.GET:
        search_form = SearchRunForm(request.GET)
        search_form.populate(product_id=request.GET.get('product'))
        search_form.is_valid()
    else:
        search_form = SearchRunForm()

    context_data = {
        'query_result': query_result,
        'search_form': search_form,
    }
    return render(request, 'run/all.html', context_data)


def run_queryset_from_querystring(querystring):
    """Setup a run queryset from a querystring.

    A querystring is used in several places in front-end
    to query a list of runs.
    """
    # 'name=alice&age=20' => {'name': 'alice', 'age': ''}
    filter_keywords = dict(k.split('=') for k in querystring.split('&'))
    # get rid of empty values and several other noisy names
    if "page_num" in filter_keywords:
        filter_keywords.pop('page_num')
    if "page_size" in filter_keywords:
        filter_keywords.pop('page_size')

    filter_keywords = dict(
        (str(k), v) for (k, v) in filter_keywords.items() if v.strip())

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
    column_names = [
        '',
        'run_id',
        'summary',
        'manager__username',
        'default_tester__username',
        'start_date',
        'build__name',
        'stop_date',
        'total_num_caseruns',
        'failure_caseruns_percent',
        'successful_caseruns_percent',
    ]

    test_plan = TestPlan.objects.get(plan_id=plan_id)
    form = PlanFilterRunForm(request.GET)

    if form.is_valid():
        queryset = test_plan.run.filter(**form.cleaned_data)
        queryset = queryset.select_related(
            'build', 'manager', 'default_tester').order_by('-pk')

        data_table_result = DataTableResult(request.GET, queryset, column_names)
        response_data = data_table_result.get_response_data()
        searched_runs = response_data['querySet']

        # Get associated statistics data
        run_filters = dict(('run__{0}'.format(key), value)
                           for key, value in form.cleaned_data.items())

        query_set = TestCaseRun.objects.filter(
            case_run_status=TestCaseRunStatus.id_failed(),
            **run_filters
        ).values(
            'run', 'case_run_status'
        ).annotate(
            count=Count('pk')
        ).order_by('run', 'case_run_status')
        failure_subtotal = magic_convert(query_set, key_name='run', value_name='count')

        query_set = TestCaseRun.objects.filter(
            case_run_status=TestCaseRunStatus.id_passed(),
            **run_filters
        ).values(
            'run', 'case_run_status'
        ).annotate(
            count=Count('pk')
        ).order_by('run', 'case_run_status')
        success_subtotal = magic_convert(query_set, key_name='run', value_name='count')

        query_set = TestCaseRun.objects.filter(
            **run_filters
        ).values('run').annotate(
            count=Count('case')
        ).order_by('run')
        cases_subtotal = magic_convert(query_set, key_name='run', value_name='count')

        for run in searched_runs:
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
        response_data = {
            'sEcho': int(request.GET.get('sEcho', 0)),
            'iTotalRecords': 0,
            'iTotalDisplayRecords': 0,
            'querySet': TestRun.objects.none(),
        }

    json_data = render_to_string(template_name, response_data, request=request)
    return HttpResponse(json_data, content_type='application/json')


@require_GET
def ajax_search(request, template_name='run/common/json_runs.txt'):
    """Response request to search test runs from Search Runs"""
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
            'plan',
            'build').only('run_id',
                          'summary',
                          'manager__username',
                          'default_tester__id',
                          'default_tester__username',
                          'plan__name',
                          'env_value',
                          'build__product__name',
                          'stop_date',
                          'product_version__value')

        # Further optimize by adding caserun attributes:
        column_names = [
            '',
            'run_id',
            'summary',
            'manager__username',
            'default_tester__username',
            'plan',
            'build__product__name',
            'product_version',
            'total_num_caseruns',
            'stop_date',
            'completed',
        ]

        data_table_result = DataTableResult(request.GET, trs, column_names)
        response_data = data_table_result.get_response_data()
        searched_runs = response_data['querySet']

        # Get associated statistics data
        run_ids = [run.pk for run in searched_runs]
        qs = TestCaseRun.objects.filter(
            run__in=run_ids
        ).values(
            'run'
        ).annotate(
            cases_count=Count('case')
        )
        cases_subtotal = magic_convert(qs, key_name='run', value_name='cases_count')

        for run in searched_runs:
            run_id = run.pk
            cases_count = cases_subtotal.get(run_id, 0)
            run.nitrate_stats = {
                'cases': cases_count,
            }
    else:
        response_data = {
            'sEcho': int(request.GET.get('sEcho', 0)),
            'iTotalRecords': 0,
            'iTotalDisplayRecords': 0,
            'runs': TestRun.objects.none(),
        }

    json_data = render_to_string(template_name, response_data, request=request)
    return HttpResponse(json_data, content_type='application/json')


def open_run_get_case_runs(request, run):
    """Prepare for case runs list in a TestRun page

    This is an internal method. Do not call this directly.
    """
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
    tcrs = tcrs.annotate(num_bug=Count('case_run_bug', distinct=True))

    # todo: is this last distinct necessary
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
    content_type = ContentType.objects.get_for_model(TestCaseRun)
    query_set = Comment.objects.filter(
        content_type=content_type,
        site_id=settings.SITE_ID,
        object_pk__in=case_run_ids,
        is_removed=False).values('object_pk').annotate(comment_count=Count('pk')).order_by(
            'object_pk')

    result = ((int(row['object_pk']), row['comment_count']) for row in query_set)
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

    # Get the test run
    try:
        # 1. get test run itself
        test_run = TestRun.objects.select_related().get(run_id=run_id)
    except ObjectDoesNotExist:
        raise Http404

    # Get the test case runs belong to the run
    # 2. get test run's all case runs
    test_case_runs = open_run_get_case_runs(request, test_run)

    case_run_status = TestCaseRunStatus.objects.only('pk', 'name').order_by('pk')

    # Count the status
    # 3. calculate number of case runs of each status
    status_stats_result = test_run.stats_caseruns_status(case_run_status)

    # Get the test case run bugs summary
    # 6. get the number of bugs of this run
    test_case_run_bugs_count = test_run.get_bug_count()

    # Get tag list of testcases
    # 7. get tags
    # Get the list of testcases belong to the run
    test_cases = [test_case_run.case_id for test_case_run in test_case_runs]
    tags = Tag.objects.filter(case__in=test_cases).values_list('name', flat=True)
    tags = list(set(tags))
    tags.sort()

    def walk_case_runs():
        """Walking case runs for helping rendering case runs table"""
        priorities = dict(Priority.objects.values_list('pk', 'value'))
        testers, assignees = open_run_get_users(test_case_runs)
        comments_subtotal = open_run_get_comments_subtotal(
            [cr.pk for cr in test_case_runs])
        case_run_status = TestCaseRunStatus.get_names()

        for case_run in test_case_runs:
            yield (case_run,
                   testers.get(case_run.tested_by_id, None),
                   assignees.get(case_run.assignee_id, None),
                   priorities.get(case_run.case.priority_id),
                   case_run_status[case_run.case_run_status_id],
                   comments_subtotal.get(case_run.pk, 0))

    context_data = {
        'test_run': test_run,
        'from_plan': request.GET.get('from_plan', False),
        'test_case_runs': walk_case_runs(),
        'test_case_runs_count': len(test_case_runs),
        'status_stats': status_stats_result,
        'test_case_run_bugs_count': test_case_run_bugs_count,
        'test_case_run_status': case_run_status,
        'priorities': Priority.objects.all(),
        'case_own_tags': tags,
        'bug_trackers': BugSystem.objects.all(),
    }
    return render(request, template_name, context_data)


@permission_required('testruns.change_testrun')
def edit(request, run_id, template_name='run/edit.html'):
    """Edit test plan view"""

    try:
        test_run = TestRun.objects.select_related().get(run_id=run_id)
    except ObjectDoesNotExist:
        raise Http404

    # If the form is submitted
    if request.method == "POST":
        form = EditRunForm(request.POST)
        form.populate(product_id=request.POST.get('product', test_run.plan.product_id))

        # FIXME: Error handler
        if form.is_valid():
            # detect if auto_update_run_status field is changed by user when
            # edit testrun.
            auto_update_changed = False
            if test_run.auto_update_run_status \
                    != form.cleaned_data['auto_update_run_status']:
                auto_update_changed = True

            # detect if finished field is changed by user when edit testrun.
            finish_field_changed = False
            if test_run.stop_date and not form.cleaned_data['finished']:
                finish_field_changed = True
                is_finish = False
            elif not test_run.stop_date and form.cleaned_data['finished']:
                finish_field_changed = True
                is_finish = True

            test_run.summary = form.cleaned_data['summary']
            # Permission hack
            if test_run.manager == request.user or test_run.plan.author == request.user:
                test_run.manager = form.cleaned_data['manager']
            test_run.default_tester = form.cleaned_data['default_tester']
            test_run.build = form.cleaned_data['build']
            test_run.product_version = form.cleaned_data['product_version']
            test_run.notes = form.cleaned_data['notes']
            test_run.estimated_time = form.cleaned_data['estimated_time']
            test_run.auto_update_run_status = form.cleaned_data[
                'auto_update_run_status']
            test_run.save()
            if auto_update_changed:
                test_run.update_completion_status(is_auto_updated=True)
            if finish_field_changed:
                test_run.update_completion_status(is_auto_updated=False,
                                                  is_finish=is_finish)
            return HttpResponseRedirect(
                reverse('testruns-get', args=[run_id, ])
            )
    else:
        # Generate a blank form
        form = EditRunForm(initial={
            'summary': test_run.summary,
            'manager': test_run.manager.email,
            'default_tester': (test_run.default_tester and
                               test_run.default_tester.email or None),
            'product': test_run.build.product_id,
            'product_version': test_run.product_version_id,
            'build': test_run.build_id,
            'notes': test_run.notes,
            'finished': test_run.stop_date,
            'estimated_time': test_run.estimated_time,
            'auto_update_run_status': test_run.auto_update_run_status,
        })
        form.populate(product_id=test_run.build.product_id)

    context_data = {
        'test_run': test_run,
        'form': form,
    }
    return render(request, template_name, context_data)


@permission_required('testruns.change_testcaserun')
def execute(request, run_id, template_name='run/execute.html'):
    """Execute test run"""
    return get(request, run_id, template_name)


class TestRunReportView(TemplateView, TestCaseRunDataMixin):
    """Test Run report"""

    template_name = 'run/report.html'

    def get(self, request, run_id):
        self.run_id = run_id
        return super(TestRunReportView, self).get(request, run_id)

    def get_context_data(self, **kwargs):
        """Generate report for specific TestRun

        There are four data source to generate this report.
        1. TestRun
        2. Test case runs included in the TestRun
        3. Comments associated with each test case run
        4. Statistics
        5. bugs
        """
        run = TestRun.objects.select_related('manager', 'plan').get(
            pk=self.run_id)

        case_runs = TestCaseRun.objects.filter(
            run=run
        ).select_related(
            'case_run_status', 'case', 'tested_by'
        ).only(
            'close_date',
            'case_run_status__name',
            'case__category__name',
            'case__summary', 'case__is_automated',
            'case__is_automated_proposed',
            'tested_by__username'
        )
        mode_stats = self.stats_mode_case_runs(case_runs)
        summary_stats = self.get_summary_stats(case_runs)

        test_case_run_bugs = []
        bug_system_types = {}
        for _bug in get_run_bug_ids(self.run_id):
            # format the bug URLs based on DB settings
            test_case_run_bugs.append((
                _bug['bug_id'],
                _bug['bug_system__url_reg_exp'] % _bug['bug_id'],
            ))
            # find out all unique bug tracking systems which were used to record
            # bugs in this particular test run. we use this data for reporting
            if _bug['bug_system'] not in bug_system_types:
                # store a tracker type object for producing the report URL
                tracker_class = IssueTrackerType.from_name(_bug['bug_system__tracker_type'])
                bug_system = BugSystem.objects.get(pk=_bug['bug_system'])
                tracker = tracker_class(bug_system)
                bug_system_types[_bug['bug_system']] = (tracker, [])

            # store the list of bugs as well
            bug_system_types[_bug['bug_system']][1].append(_bug['bug_id'])

        # list of URLs which opens all bugs reported to every different
        # issue tracker used in this test run
        report_urls = []
        for (issue_tracker, ids) in bug_system_types.values():
            report_url = issue_tracker.all_issues_link(ids)
            # if IT doesn't support this feature or report url is not configured
            # the above method will return None
            if report_url:
                report_urls.append((issue_tracker.tracker.name, report_url))

        case_run_bugs = self.get_case_runs_bugs(run.pk)
        comments = self.get_case_runs_comments(run.pk)

        for case_run in case_runs:
            bugs = case_run_bugs.get(case_run.pk, ())
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

        def add(self):
            if not self.request.user.has_perm('testcases.add_bug'):
                return JsonResponse({'rc': 1, 'response': 'Permission denied'})

            bug_id = request.GET.get('bug_id')
            bug_system_id = request.GET.get('bug_system_id')

            try:
                validate_bug_id(bug_id, bug_system_id)
            except ValidationError as error:
                return JsonResponse({'rc': 1,
                                     'response': str(error)})

            bz_external_track = True if request.GET.get('bz_external_track',
                                                        False) else False

            try:
                tcr.add_bug(bug_id=bug_id,
                            bug_system_id=bug_system_id,
                            bz_external_track=bz_external_track)
            except Exception as error:
                msg = str(error) if str(error) else 'Failed to add bug %s' % bug_id
                return JsonResponse({'rc': 1,
                                     'response': msg})

            return JsonResponse({'rc': 0,
                                 'response': 'ok',
                                 'run_bug_count': self.get_run_bug_count(),
                                 'caserun_bugs_count': self.case_run.get_bugs_count()})

        def file(self):
            bug_system_id = request.GET.get('bug_system_id')
            bug_system = BugSystem.objects.get(pk=bug_system_id)

            if bug_system.base_url:
                tracker = IssueTrackerType.from_name(bug_system.tracker_type)(bug_system)
                url = tracker.report_issue_from_testcase(self.case_run)
                response = {'rc': 0, 'response': url}

            response = {'rc': 1, 'response': 'Enable reporting to this Issue Tracker '
                                             'by configuring its base_url!'}
            return JsonResponse(response)

        def remove(self):
            if not self.request.user.has_perm('testcases.delete_bug'):
                response = {'rc': 1, 'response': 'Permission denied'}
                return self.render(response=response)

            try:
                bug_id = self.request.GET.get('bug_id')
                run_id = self.request.GET.get('case_run')
                self.case_run.remove_bug(bug_id, run_id)
            except ObjectDoesNotExist as error:
                return JsonResponse({'rc': 1, 'response': str(error)})

            return JsonResponse({'rc': 0,
                                 'response': 'ok',
                                 'run_bug_count': self.get_run_bug_count()})

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
        return JsonResponse({'rc': 1,
                             'response': 'Unrecognizable actions'})

    func = getattr(crba, request.GET['a'])
    return func()


@require_POST
def new_run_with_caseruns(request, run_id, template_name='run/clone.html'):
    """Clone cases from filter caserun"""

    test_run = get_object_or_404(TestRun, run_id=run_id)

    if request.POST.get('case_run'):
        test_case_runs = test_run.case_run.filter(pk__in=request.POST.getlist('case_run'))
    else:
        test_case_runs = []

    if not test_case_runs:
        messages.add_message(request,
                             messages.ERROR,
                             _('At least one TestCase is required'))
        return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))

    estimated_time = reduce(lambda x, y: x + y,
                            [tcr.case.estimated_time for tcr in test_case_runs])

    if not request.POST.get('submit'):
        form = RunCloneForm(initial={
            'summary': test_run.summary,
            'notes': test_run.notes, 'manager': test_run.manager.email,
            'product': test_run.plan.product_id,
            'product_version': test_run.product_version_id,
            'build': test_run.build_id,
            'default_tester':
                test_run.default_tester_id and test_run.default_tester.email or '',
            'estimated_time': estimated_time,
            'use_newest_case_text': True,
        })

        form.populate(product_id=test_run.plan.product_id)

        context_data = {
            'clone_form': form,
            'test_run': test_run,
            'cases_run': test_case_runs,
        }
        return render(request, template_name, context_data)


@permission_required('testruns.change_testrun')
def change_status(request, run_id):
    """Change test run finished or running"""
    test_run = get_object_or_404(TestRun, run_id=run_id)

    if request.GET.get('finished') == '1':
        test_run.update_completion_status(is_auto_updated=False, is_finish=True)
    else:
        test_run.update_completion_status(is_auto_updated=False, is_finish=False)

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
        test_cases_ids = request.POST.getlist('case')
        if not test_cases_ids:
            # user clicked Update button without selecting new Test Cases
            # to be dded to TestRun
            messages.add_message(request,
                                 messages.ERROR,
                                 _('At least one TestCase is required'))
            return HttpResponseRedirect(reverse('add-cases-to-run', args=[run_id]))

        try:
            test_cases_ids = list(map(int, test_cases_ids))
        except (ValueError, TypeError):
            # this will happen only on malicious requests
            messages.add_message(request,
                                 messages.ERROR,
                                 _('TestCase ID is not a valid integer'))
            return HttpResponseRedirect(reverse('add-cases-to-run', args=[run_id]))

        try:
            test_run = TestRun.objects.select_related('plan').only('plan__plan_id').get(
                run_id=run_id)
        except ObjectDoesNotExist:
            raise Http404

        test_case_runs_ids = test_run.case_run.values_list('case', flat=True)

        # avoid add cases that are already in current run with pk run_id
        test_cases_ids = set(test_cases_ids) - set(test_case_runs_ids)

        test_plan = test_run.plan
        test_cases = test_run.plan.case.filter(case_status__name='CONFIRMED').select_related(
            'default_tester').only('default_tester__id', 'estimated_time').filter(
                case_id__in=test_cases_ids)

        estimated_time = reduce(lambda x, y: x + y,
                                (test_case.estimated_time for test_case in test_cases))
        test_run.estimated_time = test_run.estimated_time + estimated_time
        test_run.save(update_fields=['estimated_time'])

        if request.POST.get('_use_plan_sortkey'):
            test_case_pks = (test_case.pk for test_case in test_cases)
            query_set = TestCasePlan.objects.filter(
                plan=test_plan, case__in=test_case_pks).values('case', 'sortkey')
            sort_keys_in_plan = dict((row['case'], row['sortkey']) for row in query_set.iterator())
            for test_case in test_cases:
                sort_key = sort_keys_in_plan.get(test_case.pk, 0)
                test_run.add_case_run(case=test_case, sortkey=sort_key)
        else:
            for test_case in test_cases:
                test_run.add_case_run(case=test_case)

        return HttpResponseRedirect(reverse('testruns-get',
                                            args=[test_run.run_id, ]))

    def get(self, request, run_id):
        # information about TestRun, used in the page header
        test_run = TestRun.objects.select_related(
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
            plan_id=test_run.plan,
            case__case_status=TestCaseStatus.objects.filter(name='CONFIRMED').first().pk
        ).order_by('case')  # order b/c of PostgreSQL

        # also grab a list of all TestCase IDs which are already present in the
        # current TestRun so we can mark them as disabled and not allow them to
        # be selected
        etcrs_id = TestCaseRun.objects.filter(run=run_id).values_list('case', flat=True)

        data = {
            'test_run': test_run,
            'confirmed_cases': rows,
            'confirmed_cases_count': rows.count(),
            'test_case_runs_count': len(etcrs_id),
            'exist_case_run_ids': etcrs_id,
        }

        return render(request, self.template_name, data)


@require_GET
def cc(request, run_id):  # pylint: disable=invalid-name
    """Add or remove cc from a test run"""

    test_run = get_object_or_404(TestRun, run_id=run_id)
    action = request.GET.get('do')
    username_or_email = request.GET.get('user')
    context_data = {'test_run': test_run, 'is_ajax': True}

    if action:
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
                if action == 'add':
                    test_run.add_cc(user=user)

                if action == 'remove':
                    test_run.remove_cc(user=user)

    return render(request, 'run/get_cc.html', context_data)


@require_POST
def update_case_run_text(request, run_id):
    """Update the IDLE cases to newest text"""

    test_run = get_object_or_404(TestRun, run_id=run_id)

    if request.POST.get('case_run'):
        test_case_runs = test_run.case_run.filter(pk__in=request.POST.getlist('case_run'))
    else:
        test_case_runs = test_run.case_run.all()

    test_case_runs = test_case_runs.filter(case_run_status__name='IDLE')

    count = 0
    updated_test_case_runs = ''
    for test_case_run in test_case_runs:
        latest_text = test_case_run.latest_text().case_text_version
        if test_case_run.case_text_version != latest_text:
            count += 1
            updated_test_case_runs += '<li>%s: %s -> %s</li>' % (
                test_case_run.case.summary, test_case_run.case_text_version, latest_text
            )
            test_case_run.case_text_version = latest_text
            test_case_run.save()

    info = "<p>%s</p><ul>%s</ul>" % (_("%d CaseRun(s) updated:") % count, updated_test_case_runs)
    message_level = messages.INFO
    if count:
        message_level = messages.SUCCESS

    messages.add_message(request, message_level, info)
    return HttpResponseRedirect(reverse('testruns-get', args=[run_id]))


@require_GET
def env_value(request):
    """Run environment property edit function"""
    test_runs = TestRun.objects.filter(run_id__in=request.GET.getlist('run_id'))

    class RunEnvActions(object):
        def __init__(self, request, test_runs):
            self.__all__ = ['add', 'remove', 'change']
            self.ajax_response = {'rc': 0, 'response': 'ok'}
            self.request = request
            self.test_runs = test_runs

        def has_no_perm(self, perm):
            if not self.request.user.has_perm('testruns.' + perm + '_envrunvaluemap'):
                return {'rc': 1, 'response': 'Permission deined - %s' % perm}

            return False

        def add(self):
            chk_perm = self.has_no_perm('add')

            if chk_perm:
                return HttpResponse(json.dumps(chk_perm))

            try:
                value = self.get_env_value(request.GET.get('env_value_id'))
                for test_run in self.test_runs:
                    _, created = test_run.add_env_value(env_value=value)

                    if not created:
                        self.ajax_response = {
                            'rc': 1,
                            'response': 'The value is exist for this run'
                        }
            except ObjectDoesNotExist as errors:
                self.ajax_response = {'rc': 1, 'response': errors}

            fragment = render(request, "run/get_environment.html",
                              {"test_run": self.test_runs[0], "is_ajax": True})
            self.ajax_response.update({  # pylint: disable=objects-update-used
                                       "fragment": str(fragment.content,
                                                       encoding=settings.DEFAULT_CHARSET)})
            return JsonResponse(self.ajax_response)

        def remove(self):
            chk_perm = self.has_no_perm('delete')
            if chk_perm:
                return HttpResponse(json.dumps(chk_perm))

            for test_run in self.test_runs:
                test_run.remove_env_value(env_value=self.get_env_value(
                    request.GET.get('env_value_id')
                ))

            return JsonResponse(self.ajax_response)

        def change(self):
            chk_perm = self.has_no_perm('change')
            if chk_perm:
                return JsonResponse(chk_perm)

            for test_run in self.test_runs:
                test_run.remove_env_value(env_value=self.get_env_value(
                    request.GET.get('old_env_value_id')
                ))
                test_run.add_env_value(env_value=self.get_env_value(
                    request.GET.get('new_env_value_id')
                ))

            return JsonResponse(self.ajax_response)

        @staticmethod
        def get_env_value(env_value_id):
            return EnvValue.objects.get(id=env_value_id)

    run_env_actions = RunEnvActions(request, test_runs)

    if request.GET.get('a') not in run_env_actions.__all__:
        ajax_response = {'rc': 1, 'response': 'Unrecognizable actions'}
        return JsonResponse(ajax_response)

    func = getattr(run_env_actions, request.GET['a'])
    return func()


def view_caseruns(request):
    """View that search caseruns."""
    queries = request.GET
    r_form = RunForm(queries)
    r_form.populate(queries)
    context = {}
    if r_form.is_valid():
        runs = SmartDjangoQuery(r_form.cleaned_data, TestRun.__name__).evaluate()
        case_runs = get_caseruns_of_runs(runs, queries)
        context['test_case_runs'] = case_runs
        context['runs'] = runs
    return render(request, 'report/caseruns.html', context)


def get_caseruns_of_runs(runs, kwargs=None):
    """
    Filtering argument -
        priority
        tester
        plan tag
    """

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


@method_decorator(permission_required('testruns.change_testcaserun'), name='dispatch')
class UpdateAssigneeView(View):
    """Updates TestCaseRun.assignee. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        assignee = request.POST.get('assignee')
        try:
            user = User.objects.get(username=assignee)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=assignee)
            except User.DoesNotExist:
                return JsonResponse({'rc': 1,
                                     'response': _('User %s not found!' % assignee)},
                                    status=HTTPStatus.NOT_FOUND)

        object_ids = request.POST.getlist('ids[]')

        for caserun_pk in object_ids:
            test_case_run = get_object_or_404(TestCaseRun, pk=int(caserun_pk))
            test_case_run.assignee = user
            test_case_run.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})


@method_decorator(permission_required('testruns.change_testcaserun'), name='dispatch')
class UpdateCaseRunStatusView(View):
    """Updates TestCaseRun.case_run_status_id. Called from the front-end."""

    http_method_names = ['post']

    def post(self, request):
        status_id = int(request.POST.get('status_id'))
        object_ids = request.POST.getlist('object_pk[]')

        for caserun_pk in object_ids:
            test_case_run = get_object_or_404(TestCaseRun, pk=int(caserun_pk))
            test_case_run.case_run_status_id = status_id
            test_case_run.save()

        return JsonResponse({'rc': 0, 'response': 'ok'})
