# -*- coding: utf-8 -*-

import datetime
import json
import itertools

from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView

from django_comments.models import Comment

from tcms.core import forms
from tcms.core.logs.models import TCMSLogModel
from tcms.core.responses import HttpJSONResponse
from tcms.core.utils.raw_sql import RawSQL
from tcms.core.utils import DataTableResult
from tcms.core.views import Prompt
from tcms.search import remove_from_request_path
from tcms.search.order import order_case_queryset
from tcms.testcases import actions
from tcms.testcases import data
from tcms.testcases.models import TestCase, TestCaseStatus, \
    TestCaseAttachment, TestCasePlan, TestCaseBugSystem, \
    TestCaseBug, TestCaseText, TestCaseComponent
from tcms.management.models import Priority, TestTag
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.testcases.forms import CaseAutomatedForm, NewCaseForm, \
    SearchCaseForm, CaseFilterForm, EditCaseForm, CaseNotifyForm, \
    CloneCaseForm, CaseBugForm, CaseTagForm
from tcms.testplans.forms import SearchPlanForm
from tcms.utils.dict_utils import create_dict_from_query
from fields import CC_LIST_DEFAULT_DELIMITER


MODULE_NAME = "testcases"

TESTCASE_OPERATION_ACTIONS = (
    'search', 'sort', 'update',
    'remove',  # including remove tag from cases
    'add',  # including add tag to cases
    'change',
    'delete_cases',  # unlink cases from a TestPlan
)


# _____________________________________________________________________________
# helper functions


def plan_from_request_or_none(request, pk_enough=False):
    '''Get TestPlan from REQUEST

    This method relies on the existence of from_plan within REQUEST.

    Arguments:
    - pk_enough: a choice for invoker to determine whether the ID is enough.
    '''
    tp_id = request.POST.get("from_plan") or request.GET.get("from_plan")
    if tp_id:
        if pk_enough:
            try:
                tp = int(tp_id)
            except ValueError:
                tp = None
        else:
            tp = get_object_or_404(TestPlan, plan_id=tp_id)
    else:
        tp = None
    return tp


def update_case_email_settings(tc, n_form):
    """Update testcase's email settings."""

    tc.emailing.notify_on_case_update = n_form.cleaned_data[
        'notify_on_case_update']
    tc.emailing.notify_on_case_delete = n_form.cleaned_data[
        'notify_on_case_delete']
    tc.emailing.auto_to_case_author = n_form.cleaned_data[
        'author']
    tc.emailing.auto_to_case_tester = n_form.cleaned_data[
        'default_tester_of_case']
    tc.emailing.auto_to_run_manager = n_form.cleaned_data[
        'managers_of_runs']
    tc.emailing.auto_to_run_tester = n_form.cleaned_data[
        'default_testers_of_runs']
    tc.emailing.auto_to_case_run_assignee = n_form.cleaned_data[
        'assignees_of_case_runs']
    tc.emailing.save()

    default_tester = n_form.cleaned_data['default_tester_of_case']
    if (default_tester and tc.default_tester_id):
        tc.emailing.auto_to_case_tester = True

    # Continue to update CC list
    valid_emails = n_form.cleaned_data['cc_list']
    tc.emailing.update_cc_list(valid_emails)


def group_case_bugs(bugs):
    """Group bugs using bug_id."""
    bugs = itertools.groupby(bugs, lambda b: b.bug_id)
    bugs = [(pk, list(_bugs)) for pk, _bugs in bugs]
    return bugs


def create_testcase(request, form, tp):
    """Create testcase"""
    tc = TestCase.create(author=request.user, values=form.cleaned_data)
    tc.add_text(case_text_version=1,
                author=request.user,
                action=form.cleaned_data['action'],
                effect=form.cleaned_data['effect'],
                setup=form.cleaned_data['setup'],
                breakdown=form.cleaned_data['breakdown'])

    # Assign the case to the plan
    if tp:
        tc.add_to_plan(plan=tp)

    # Add components into the case
    for component in form.cleaned_data['component']:
        tc.add_component(component=component)
    return tc


@require_POST
@permission_required('testcases.change_testcase')
def automated(request):
    """Change the automated status for cases

    Parameters:
    - a: Actions
    - case: IDs for case_id
    - o_is_automated: Status for is_automated
    - o_is_automated_proposed: Status for is_automated_proposed

    Returns:
    - Serialized JSON

    """
    ajax_response = {'rc': 0, 'response': 'ok'}

    form = CaseAutomatedForm(request.POST)
    if form.is_valid():
        tcs = get_selected_testcases(request)

        if form.cleaned_data['a'] == 'change':
            if isinstance(form.cleaned_data['is_automated'], int):
                # FIXME: inconsistent operation updating automated property
                # upon TestCases. Other place to update property upon
                # TestCase via Model.save, that will trigger model
                #        singal handlers.
                tcs.update(is_automated=form.cleaned_data['is_automated'])
            if isinstance(form.cleaned_data['is_automated_proposed'], bool):
                tcs.update(is_automated_proposed=form.cleaned_data['is_automated_proposed'])
    else:
        ajax_response['rc'] = 1
        ajax_response['response'] = forms.errors_to_list(form)

    return HttpResponse(json.dumps(ajax_response))


@permission_required('testcases.add_testcase')
def new(request, template_name='case/new.html'):
    """New testcase"""
    tp = plan_from_request_or_none(request)
    # Initial the form parameters when write new case from plan
    if tp:
        default_form_parameters = {
            'product': tp.product_id,
            'component': tp.component.defer('id').values_list('pk', flat=True),
            'is_automated': '0',
        }
    # Initial the form parameters when write new case directly
    else:
        default_form_parameters = {'is_automated': '0'}

    if request.method == "POST":
        form = NewCaseForm(request.POST)
        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        else:
            form.populate()

        if form.is_valid():
            tc = create_testcase(request, form, tp)

            class ReturnActions(object):
                def __init__(self, case, plan):
                    self.__all__ = ('_addanother', '_continue', '_returntocase', '_returntoplan')
                    self.case = case
                    self.plan = plan

                def _continue(self):
                    if self.plan:
                        return HttpResponseRedirect(
                            '%s?from_plan=%s' % (reverse('testcases-edit',
                                                         args=[self.case.case_id]),
                                                 self.plan.plan_id))

                    return HttpResponseRedirect(
                        reverse('testcases-edit', args=[tc.case_id]))

                def _addanother(self):
                    form = NewCaseForm(initial=default_form_parameters)

                    if tp:
                        form.populate(product_id=self.plan.product_id)

                    return form

                def _returntocase(self):
                    if self.plan:
                        return HttpResponseRedirect(
                            '%s?from_plan=%s' % (reverse('testcases-get',
                                                         args=[self.case.pk]),
                                                 self.plan.plan_id))

                    return HttpResponseRedirect(
                        reverse('testcases-get', args=[self.case.pk]))

                def _returntoplan(self):
                    if not self.plan:
                        raise Http404

                    return HttpResponseRedirect(
                        '%s#reviewcases' % reverse('test_plan_url_short',
                                                   args=[self.plan.pk]))

            # Genrate the instance of actions
            ras = ReturnActions(case=tc, plan=tp)
            for ra_str in ras.__all__:
                if request.POST.get(ra_str):
                    func = getattr(ras, ra_str)
                    break
            else:
                func = ras._returntocase

            # Get the function and return back
            result = func()
            if isinstance(result, HttpResponseRedirect):
                return result
            else:
                # Assume here is the form
                form = result

    # Initial NewCaseForm for submit
    else:
        tp = plan_from_request_or_none(request)
        form = NewCaseForm(initial=default_form_parameters)
        if tp:
            form.populate(product_id=tp.product_id)

    context_data = {
        'test_plan': tp,
        'form': form
    }
    return render(request, template_name, context_data)


def get_testcaseplan_sortkey_pk_for_testcases(plan, tc_ids):
    '''Get each TestCase' sortkey and related TestCasePlan's pk'''
    qs = TestCasePlan.objects.filter(case__in=tc_ids)
    if plan is not None:
        qs = qs.filter(plan__pk=plan.pk)
    qs = qs.values('pk', 'sortkey', 'case')
    return dict([(item['case'], {
        'testcaseplan_pk': item['pk'],
        'sortkey': item['sortkey']
    }) for item in qs])


def calculate_number_of_bugs_for_testcases(tc_ids):
    '''Calculate the number of bugs for each TestCase

    Arguments:
    - tc_ids: a list of tuple of TestCases' IDs
    '''
    qs = TestCaseBug.objects.filter(case__in=tc_ids)
    qs = qs.values('case').annotate(total_count=Count('pk'))
    return dict([(item['case'], item['total_count']) for item in qs])


def calculate_for_testcases(plan, testcases):
    '''Calculate extra data for TestCases

    Attach TestCasePlan.sortkey, TestCasePlan.pk, and the number of bugs of
    each TestCase.

    Arguments:
    - plan: the TestPlan containing searched TestCases. None means testcases
      are not limited to a specific TestPlan.
    - testcases: a queryset of TestCases.
    '''
    tc_ids = [tc.pk for tc in testcases]
    sortkey_tcpkan_pks = get_testcaseplan_sortkey_pk_for_testcases(
        plan, tc_ids)
    num_bugs = calculate_number_of_bugs_for_testcases(tc_ids)

    # FIXME: strongly recommended to upgrade to Python +2.6
    for tc in testcases:
        data = sortkey_tcpkan_pks.get(tc.pk, None)
        if data:
            setattr(tc, 'cal_sortkey', data['sortkey'])
        else:
            setattr(tc, 'cal_sortkey', None)
        if data:
            setattr(tc, 'cal_testcaseplan_pk', data['testcaseplan_pk'])
        else:
            setattr(tc, 'cal_testcaseplan_pk', None)
        setattr(tc, 'cal_num_bugs', num_bugs.get(tc.pk, None))

    return testcases


def get_case_status(template_type):
    '''Get part or all TestCaseStatus according to template type'''
    confirmed_status_name = 'CONFIRMED'
    if template_type == 'case':
        d_status = TestCaseStatus.objects.filter(name=confirmed_status_name)
    elif template_type == 'review_case':
        d_status = TestCaseStatus.objects.exclude(name=confirmed_status_name)
    else:
        d_status = TestCaseStatus.objects.all()
    return d_status


@require_POST
def build_cases_search_form(request, populate=None, plan=None):
    '''Build search form preparing for quering TestCases'''
    # Intial the plan in plan details page
    if request.POST.get('from_plan'):
        SearchForm = CaseFilterForm
    else:
        SearchForm = SearchCaseForm

    # Initial the form and template
    action = request.POST.get('a')
    if action in TESTCASE_OPERATION_ACTIONS:
        search_form = SearchForm(request.POST)
        request.session['items_per_page'] = \
            request.POST.get('items_per_page', settings.DEFAULT_PAGE_SIZE)
    else:
        d_status = get_case_status(request.POST.get('template_type'))
        d_status_ids = d_status.values_list('pk', flat=True)
        items_per_page = request.session.get('items_per_page',
                                             settings.DEFAULT_PAGE_SIZE)
        search_form = SearchForm(initial={'case_status': d_status_ids,
                                          'items_per_page': items_per_page})

    if populate:
        if request.POST.get('product'):
            search_form.populate(product_id=request.POST['product'])
        elif plan and plan.product_id:
            search_form.populate(product_id=plan.product_id)
        else:
            search_form.populate()

    return search_form


def paginate_testcases(request, testcases):
    '''Paginate queried TestCases

    Arguments:
    - request: django's HttpRequest from which to get pagination data
    - testcases: an object queryset representing already queried TestCases

    Return value: return the queryset for chain call
    '''
    DEFAULT_PAGE_INDEX = 1

    POST = request.POST
    page_index = int(POST.get('page_index', DEFAULT_PAGE_INDEX))
    page_size = int(POST.get('items_per_page',
                             request.session.get('items_per_page',
                                                 settings.DEFAULT_PAGE_SIZE)))
    offset = (page_index - 1) * page_size
    return testcases[offset:offset + page_size]


def query_testcases(request, plan, search_form):
    '''Query TestCases according to the criterias along with REQUEST'''
    # FIXME: search_form is not defined before being used.
    action = request.POST.get('a')
    if action in TESTCASE_OPERATION_ACTIONS and search_form.is_valid():
        tcs = TestCase.list(search_form.cleaned_data, plan)
    elif action == 'initial':
        d_status = get_case_status(request.POST.get('template_type'))
        tcs = TestCase.objects.filter(case_status__in=d_status)
    else:
        tcs = TestCase.objects.none()

    # Search the relationship
    if plan:
        tcs = tcs.filter(plan=plan)

    tcs = tcs.select_related('author',
                             'default_tester',
                             'case_status',
                             'priority',
                             'category',
                             'reviewer')
    return tcs


def sort_queried_testcases(request, testcases):
    '''Sort querid TestCases according to sort key

    Arguments:
    - request: REQUEST object
    - testcases: object of QuerySet containing queried TestCases
    '''
    order_by = request.POST.get('order_by', 'create_date')
    asc = bool(request.POST.get('asc', None))
    tcs = order_case_queryset(testcases, order_by, asc)
    # default sorted by sortkey
    tcs = tcs.order_by('testcaseplan__sortkey')
    # Resort the order
    # if sorted by 'sortkey'(foreign key field)
    case_sort_by = request.POST.get('case_sort_by')
    if case_sort_by:
        if case_sort_by not in ['sortkey', '-sortkey']:
            tcs = tcs.order_by(case_sort_by)
        elif case_sort_by == 'sortkey':
            tcs = tcs.order_by('testcaseplan__sortkey')
        else:
            tcs = tcs.order_by('-testcaseplan__sortkey')
    return tcs


def query_testcases_from_request(request, plan=None):
    '''Query TestCases according to criterias coming within REQUEST

    Arguments:
    - request: the REQUEST object.
    - plan: instance of TestPlan to restrict only those TestCases belongs to
      the TestPlan. Can be None. As you know, query from all TestCases.
    '''
    search_form = build_cases_search_form(request)
    return query_testcases(request, plan, search_form)


def get_selected_testcases(request):
    '''Get selected TestCases from client side

    TestCases are selected in two cases. One is user selects part of displayed
    TestCases, where there should be at least one variable named case, whose
    value is the TestCase Id. Another one is user selects all TestCases based
    on previous filter criterias even through there are non-displayed ones. In
    this case, another variable selectAll appears in the REQUEST. Whatever its
    value is.

    If neither variables mentioned exists, empty query result is returned.

    Arguments:
    - request: REQUEST object.
    '''
    REQ = request.POST or request.GET
    if REQ.get('selectAll', None):
        plan = plan_from_request_or_none(request)
        return query_testcases_from_request(request, plan)
    else:
        pks = [int(pk) for pk in REQ.getlist('case')]
        return TestCase.objects.filter(pk__in=pks)


def load_more_cases(request, template_name='plan/cases_rows.html'):
    '''Loading more TestCases'''
    plan = plan_from_request_or_none(request)
    cases = []
    selected_case_ids = []
    if plan is not None:
        cases = query_testcases_from_request(request, plan)
        cases = sort_queried_testcases(request, cases)
        cases = paginate_testcases(request, cases)
        cases = calculate_for_testcases(plan, cases)
        selected_case_ids = [tc.pk for tc in cases]
    context_data = {
        'test_plan': plan,
        'test_cases': cases,
        'selected_case_ids': selected_case_ids,
        'case_status': TestCaseStatus.objects.all(),
    }
    return render(request, template_name, context_data)


def get_selected_cases_ids(request):
    '''Get cases' IDs to restore the checked status after current operation

    The cases whose ID appears in REQUEST is handled, and they should be
    checked when user sees the page returned after current operation.

    If there is no case argument in REQUEST, check all. This is also the
    default behavior.

    Return values:
    - a list of IDs, which should be checked.
    - empty list, representing select all.
    '''
    REQUEST = request.POST
    if REQUEST.get('case'):
        # FIXME: why do not use list comprehension.
        return map(lambda f: int(f), REQUEST.getlist('case'))
    else:
        return []


def get_tags_from_cases(case_ids, plan=None):
    '''Get all tags from test cases

    @param cases: an iterable object containing test cases' ids
    @type cases: list, tuple

    @param plan: TestPlan object

    @return: a list containing all found tags with id and name
    @rtype: list
    '''
    query = TestTag.objects.filter(cases__in=case_ids).distinct().order_by('name')
    if plan:
        query = query.filter(cases__plan=plan)

    return query


def all(request, template_name="case/all.html"):
    """Generate the case list in search case and case zone in plan

    Parameters:
    a: Action
       -- search: Search form submitted.
       -- initial: Initial the case filter
    from_plan: Plan ID
       -- [number]: When the plan ID defined, it will build the case
    page in plan.

    """
    # Intial the plan in plan details page
    tp = plan_from_request_or_none(request)
    search_form = build_cases_search_form(request, populate=True, plan=tp)
    tcs = query_testcases(request, tp, search_form)
    tcs = sort_queried_testcases(request, tcs)
    total_cases_count = tcs.count()

    # Initial the case ids
    selected_case_ids = get_selected_cases_ids(request)

    # Get the tags own by the cases
    ttags = get_tags_from_cases((case.pk for case in tcs), tp)

    tcs = paginate_testcases(request, tcs)

    # There are several extra information related to each TestCase to be shown
    # also. This step must be the very final one, because the calculation of
    # related data requires related TestCases' IDs, that is the queryset of
    # TestCases should be evaluated in advance.
    tcs = calculate_for_testcases(tp, tcs)

    # generating a query_url with order options
    #
    # FIXME: query_url is always equivlant to None&asc=True whatever what
    # criterias specified in filter form, or just with default filter
    # conditions during loading TestPlan page.
    query_url = remove_from_request_path(request, 'order_by')
    asc = bool(request.POST.get('asc', None))
    if asc:
        query_url = remove_from_request_path(query_url, 'asc')
    else:
        query_url = '%s&asc=True' % query_url

    # Due to this method serves several sort of search requests, so before
    # rendering the search result, template should be adjusted to a proper one.
    if request.POST.get('from_plan'):
        if request.POST.get('template_type') == 'case':
            template_name = 'plan/get_cases.html'
        elif request.POST.get('template_type') == 'review_case':
            template_name = 'plan/get_review_cases.html'

    context_data = {
        'module': MODULE_NAME,
        'test_cases': tcs,
        'test_plan': tp,
        'search_form': search_form,
        'selected_case_ids': selected_case_ids,
        'case_status': TestCaseStatus.objects.all(),
        'priorities': Priority.objects.all(),
        'case_own_tags': ttags,
        'query_url': query_url,

        # Load more is a POST request, so POST parameters are required only.
        # Remember this for loading more cases with the same as criterias.
        'search_criterias': request.body,
        'total_cases_count': total_cases_count,
    }
    return render(request, template_name, context_data)


@require_GET
def search(request, template_name='case/all.html'):
    """
    generate the function of searching cases with search criteria
    """
    search_form = SearchCaseForm(request.GET)
    if request.GET.get('product'):
        search_form.populate(product_id=request.GET['product'])
    else:
        search_form.populate()

    context_data = {
        'module': MODULE_NAME,
        'search_form': search_form,
    }
    return render(request, template_name, context_data)


@require_GET
def ajax_search(request, template_name='case/common/json_cases.txt'):
    """Generate the case list in search case and case zone in plan
    """
    SearchForm = SearchCaseForm

    tp = plan_from_request_or_none(request)

    action = request.GET.get('a')

    # Initial the form and template
    if action in ('search', 'sort'):
        search_form = SearchForm(request.GET)
    else:
        # Hacking for case plan
        confirmed_status_name = 'CONFIRMED'
        # 'c' is meaning component
        template_type = request.GET.get('template_type')
        if template_type == 'case':
            d_status = TestCaseStatus.objects.filter(name=confirmed_status_name)
        elif template_type == 'review_case':
            d_status = TestCaseStatus.objects.exclude(name=confirmed_status_name)
        else:
            d_status = TestCaseStatus.objects.all()

        d_status_ids = d_status.values_list('pk', flat=True)

        search_form = SearchForm(initial={'case_status': d_status_ids})

    # Populate the form
    if request.GET.get('product'):
        search_form.populate(product_id=request.GET['product'])
    elif tp and tp.product_id:
        search_form.populate(product_id=tp.product_id)
    else:
        search_form.populate()

    # Query the database when search
    if action in ('search', 'sort') and search_form.is_valid():
        tcs = TestCase.list(search_form.cleaned_data)
    elif action == 'initial':
        tcs = TestCase.objects.filter(case_status__in=d_status)
    else:
        tcs = TestCase.objects.none()

    # Search the relationship
    if tp:
        tcs = tcs.filter(plan=tp)

    tcs = tcs.select_related(
        'author',
        'default_tester',
        'case_status',
        'priority',
        'category'
    ).only(
        'case_id',
        'summary',
        'create_date',
        'is_automated',
        'is_automated_proposed',
        'case_status__name',
        'category__name',
        'priority__value',
        'author__username',
        'default_tester__id',
        'default_tester__username'
    )
    tcs = tcs.extra(select={'num_bug': RawSQL.num_case_bugs, })

    # columnIndexNameMap is required for correct sorting behavior, 5 should be
    # product, but we use run.build.product
    column_names = [
        '',
        '',
        'case_id',
        'summary',
        'author__username',
        'default_tester__username',
        'is_automated',
        'case_status__name',
        'category__name',
        'priority__value',
        'create_date',
    ]
    return ajax_response(request, tcs, column_names, template_name)


def ajax_response(request, queryset, column_names, template_name):
    """json template for the ajax request for searching"""
    dt = DataTableResult(request.GET, queryset, column_names)

    # prepare the JSON with the response, consider using :
    # from django.template.defaultfilters import escapejs
    json_result = render_to_string(
        template_name,
        dt.get_response_data(),
        request=request)
    return HttpJSONResponse(json_result)


class SimpleTestCaseView(TemplateView, data.TestCaseViewDataMixin):
    '''Simple read-only TestCase View used in TestPlan page'''

    template_name = 'case/get_details.html'

    # NOTES: what permission is proper for this request?
    def get(self, request, case_id):
        self.case_id = case_id
        return super(SimpleTestCaseView, self).get(request, case_id)

    def get_case(self):
        cases = TestCase.objects.filter(pk=self.case_id).only('notes')
        cases = list(cases.iterator())
        return cases[0] if cases else None

    def get_context_data(self, **kwargs):
        data = super(SimpleTestCaseView, self).get_context_data(**kwargs)

        case = self.get_case()
        data['test_case'] = case
        if case is not None:
            data.update({
                'test_case_text': case.get_text_with_version(),
                'attachments': case.attachment.only('file_name'),
                'components': case.component.only('name'),
                'tags': case.tag.only('name'),
                'case_comments': self.get_case_comments(case),
            })

        return data


class TestCaseReviewPaneView(SimpleTestCaseView):
    '''Used in Reviewing Cases tab in test plan page'''

    template_name = 'case/get_details_review.html'

    def get_context_data(self, **kwargs):
        data = super(TestCaseReviewPaneView, self).get_context_data(**kwargs)
        testcase = data['test_case']
        if testcase is not None:
            logs = self.get_case_logs(testcase)
            comments = self.get_case_comments(testcase)
            data.update({
                'logs': logs,
                'case_comments': comments,
            })
        return data


class TestCaseCaseRunListPaneView(TemplateView):
    '''Display case runs list when expand a plan from case page'''

    template_name = 'case/get_case_runs_by_plan.html'

    # FIXME: what permission here?
    def get(self, request, case_id):
        self.case_id = case_id

        plan_id = self.request.GET.get('plan_id', None)
        self.plan_id = int(plan_id) if plan_id is not None else None

        this_cls = TestCaseCaseRunListPaneView
        return super(this_cls, self).get(request, case_id)

    def get_case_runs(self):
        qs = TestCaseRun.objects.filter(case=self.case_id,
                                        run__plan=self.plan_id)
        qs = qs.values(
            'pk', 'case_id', 'run_id', 'case_text_version',
            'close_date', 'sortkey',
            'tested_by__username', 'assignee__username',
            'run__plan_id', 'run__summary',
            'case__category__name', 'case__priority__value',
            'case_run_status__name',
        ).order_by('pk')
        return qs

    def get_comments_count(self, caserun_ids):
        ct = ContentType.objects.get_for_model(TestCaseRun)
        qs = Comment.objects.filter(content_type=ct,
                                    object_pk__in=caserun_ids,
                                    site_id=settings.SITE_ID,
                                    is_removed=False)
        qs = qs.values('object_pk').annotate(comment_count=Count('pk'))
        result = {}
        for item in qs.iterator():
            result[int(item['object_pk'])] = item['comment_count']
        return result

    def get_context_data(self, **kwargs):
        this_cls = TestCaseCaseRunListPaneView
        data = super(this_cls, self).get_context_data(**kwargs)

        case_runs = self.get_case_runs()

        # Get the number of each caserun's comments, and put the count into
        # comments query result.
        caserun_ids = [item['pk'] for item in case_runs]
        comments_count = self.get_comments_count(caserun_ids)
        for case_run in case_runs:
            case_run['comments_count'] = comments_count.get(case_run['pk'], 0)

        data.update({
            'case_runs': case_runs,
        })
        return data


class TestCaseSimpleCaseRunView(TemplateView, data.TestCaseRunViewDataMixin):
    '''Display caserun information in Case Runs tab in case page

    This view only shows notes, comments and logs simply. So, call it simple.
    '''

    template_name = 'case/get_details_case_case_run.html'

    # what permission here?
    def get(self, request, case_id):
        try:
            self.caserun_id = int(request.GET.get('case_run_id', None))
        except (TypeError, ValueError):
            raise Http404

        this_cls = TestCaseSimpleCaseRunView
        return super(this_cls, self).get(request, case_id)

    def get_caserun(self):
        try:
            return TestCaseRun.objects.filter(
                pk=self.caserun_id).only('notes')[0]
        except IndexError:
            raise Http404

    def get_context_data(self, **kwargs):
        this_cls = TestCaseSimpleCaseRunView
        data = super(this_cls, self).get_context_data(**kwargs)

        caserun = self.get_caserun()
        logs = self.get_caserun_logs(caserun)
        comments = self.get_caserun_comments(caserun)

        data.update({
            'test_caserun': caserun,
            'logs': logs.iterator(),
            'comments': comments.iterator(),
        })
        return data


class TestCaseCaseRunDetailPanelView(TemplateView,
                                     data.TestCaseViewDataMixin,
                                     data.TestCaseRunViewDataMixin):
    '''Display case run detail in run page'''

    template_name = 'case/get_details_case_run.html'

    def get(self, request, case_id):
        self.case_id = case_id
        try:
            self.caserun_id = int(request.GET.get('case_run_id'))
            self.case_text_version = int(request.GET.get('case_text_version'))
        except (TypeError, ValueError):
            raise Http404

        this_cls = TestCaseCaseRunDetailPanelView
        return super(this_cls, self).get(request, case_id)

    def get_context_data(self, **kwargs):
        this_cls = TestCaseCaseRunDetailPanelView
        data = super(this_cls, self).get_context_data(**kwargs)

        try:
            qs = TestCase.objects.filter(pk=self.case_id)
            qs = qs.prefetch_related('attachment',
                                     'component',
                                     'tag').only('pk')
            case = qs[0]

            qs = TestCaseRun.objects.filter(pk=self.caserun_id).order_by('pk')
            case_run = qs[0]
        except IndexError:
            raise Http404

        # Data of TestCase
        test_case_text = case.get_text_with_version(self.case_text_version)

        # Data of TestCaseRun
        caserun_comments = self.get_caserun_comments(case_run)
        caserun_logs = self.get_caserun_logs(case_run)

        caserun_status = TestCaseRunStatus.objects.values('pk', 'name')
        caserun_status = caserun_status.order_by('sortkey')
        bugs = group_case_bugs(case_run.case.get_bugs().order_by('bug_id'))

        data.update({
            'test_case': case,
            'test_case_text': test_case_text,

            'test_case_run': case_run,
            'comments_count': len(caserun_comments),
            'caserun_comments': caserun_comments,
            'caserun_logs': caserun_logs,
            'test_case_run_status': caserun_status,
            'grouped_case_bugs': bugs,
        })

        return data


def get(request, case_id, template_name='case/get.html'):
    """Get the case content"""
    # Get the case
    try:
        tc = TestCase.objects.select_related(
            'author', 'default_tester',
            'category', 'category',
            'priority', 'case_status').get(case_id=case_id)
    except ObjectDoesNotExist:
        raise Http404

    # Get the test plans
    tps = tc.plan.select_related('author', 'product', 'type').all()

    # log
    log_id = str(case_id)
    logs = TCMSLogModel.get_logs_for_model(TestCase, log_id)

    logs = itertools.groupby(logs, lambda l: l.date)
    logs = [(day, list(log_actions)) for day, log_actions in logs]
    # Get the specific test plan
    plan_id_from_request = request.GET.get('from_plan')
    if plan_id_from_request:
        try:
            tp = tps.get(pk=plan_id_from_request)
        except TestPlan.DoesNotExist:
            return Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='''This case has been removed from the plan, but you
                          can view the case detail''',
                next=reverse('testcases-get',
                             args=[case_id, ]),
            )
    else:
        tp = None

    # Get the test case runs
    tcrs = tc.case_run.select_related(
        'run', 'tested_by',
        'assignee', 'case',
        'case', 'case_run_status').all()
    tcrs = tcrs.extra(select={
        'num_bug': RawSQL.num_case_run_bugs,
    }).order_by('run__plan')
    runs_ordered_by_plan = itertools.groupby(tcrs, lambda t: t.run.plan)
    # FIXME: Just don't know why Django template does not evaluate a generator,
    # and had to evaluate the groupby generator manually like below.
    runs_ordered_by_plan = [(k, list(v)) for k, v in runs_ordered_by_plan]
    case_run_plans = [k for k, v in runs_ordered_by_plan]
    # Get the specific test case run
    if request.GET.get('case_run_id'):
        tcr = tcrs.get(pk=request.GET['case_run_id'])
    else:
        tcr = None
    case_run_plan_id = request.GET.get('case_run_plan_id', None)
    if case_run_plan_id:
        for item in runs_ordered_by_plan:
            if item[0].pk == int(case_run_plan_id):
                case_runs_by_plan = item[1]
                break
            else:
                continue
    else:
        case_runs_by_plan = None

    # Get the case texts
    tc_text = tc.get_text_with_version(
        request.GET.get('case_text_version'))
    # Switch the templates for different module
    template_types = {
        'case': 'case/get_details.html',
        # 'review_case': 'case/get_details_review.html',
        'case_run': 'case/get_details_case_run.html',
        # 'case_run_list': 'case/get_case_runs_by_plan.html',
        # 'case_case_run': 'case/get_details_case_case_run.html',
        'execute_case_run': 'run/execute_case_run.html',
    }

    if request.GET.get('template_type'):
        template_name = template_types.get(
            request.GET['template_type'], 'case')

    grouped_case_bugs = tcr and group_case_bugs(tcr.case.get_bugs())
    # Render the page
    context_data = {
        'logs': logs,
        'test_case': tc,
        'test_plan': tp,
        'test_plans': tps,
        'test_case_runs': tcrs,
        'case_run_plans': case_run_plans,
        'test_case_runs_by_plan': case_runs_by_plan,
        'test_case_run': tcr,
        'grouped_case_bugs': grouped_case_bugs,
        'test_case_text': tc_text,
        'test_case_status': TestCaseStatus.objects.all(),
        'test_case_run_status': TestCaseRunStatus.objects.all(),
        'bug_trackers': TestCaseBugSystem.objects.all(),
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
    }
    return render(request, template_name, context_data)


# TODO: better to split this method for TestPlan and TestCase respectively.
# NOTE: if you want to print cases according to case_status, you have to pass
# printable_case_status in the REQUEST. Why to do this rather than using
# case_status is that, Select All causes previous filter criteria is
# passed via REQUEST, whereas case_status must exist. So, we have to find
# a way to distinguish them for different purpose, respectively.
@require_POST
def printable(request, template_name='case/printable.html'):
    """Create the printable copy for plan/case"""
    case_pks = request.POST.getlist('case')

    if not case_pks:
        return Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one target is required.', )

    tcs = create_dict_from_query(
        TestCaseText.objects.filter(
            case__in=case_pks
        ).values(
            'case_id', 'case__summary', 'setup', 'action', 'effect', 'breakdown'
        ).order_by('case_id', '-case_text_version'),
        'case_id',
        True
    )

    context_data = {
        'test_cases': tcs,
    }
    return render(request, template_name, context_data)


@require_POST
def export(request, template_name='case/export.xml'):
    """Export the plan"""
    case_pks = request.POST.getlist('case')
    if not case_pks:
        return Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one target is required.', )

    timestamp = datetime.datetime.now()
    timestamp_str = '%02i-%02i-%02i' \
                    % (timestamp.year, timestamp.month, timestamp.day)

    context_data = {
        'data_generator': generator_proxy(case_pks),
    }

    response = render(request, template_name, context_data)

    response['Content-Disposition'] = \
        'attachment; filename=tcms-testcases-%s.xml' % timestamp_str
    return response


def generator_proxy(case_pks):
    metas = TestCase.objects.filter(
        pk__in=case_pks
    ).exclude(
        case_status__name='DISABLED'
    ).values(
        'case_id', 'summary', 'is_automated', 'notes',
        'priority__value', 'case_status__name',
        'author__email', 'default_tester__email',
        'category__name')

    component_dict = create_dict_from_query(
        TestCaseComponent.objects.filter(
            case__in=case_pks
        ).values(
            'case_id', 'component_id', 'component__name', 'component__product__name'
        ).order_by('case_id'),
        'case_id'
    )

    tag_dict = create_dict_from_query(
        TestCase.objects.filter(
            pk__in=case_pks
        ).values('case_id', 'tag__name').order_by('case_id'),
        'case_id'
    )

    plan_text_dict = create_dict_from_query(
        TestCaseText.objects.filter(
            case__in=case_pks
        ).values(
            'case_id', 'setup', 'action', 'effect', 'breakdown'
        ).order_by('case_id', '-case_text_version'),
        'case_id',
        True
    )

    for meta in metas:
        case_id = meta['case_id']
        c_meta = component_dict.get(case_id, None)
        if c_meta:
            meta['c_meta'] = c_meta

        tag = tag_dict.get(case_id, None)
        if tag:
            meta['tag'] = tag

        plan_text = plan_text_dict.get(case_id, None)
        if plan_text:
            meta['latest_text'] = plan_text

        yield meta


def update_testcase(request, tc, tc_form):
    '''Updating information of specific TestCase

    This is called by views.edit internally. Don't call this directly.

    Arguments:
    - tc: instance of a TestCase being updated
    - tc_form: instance of django.forms.Form, holding validated data.
    '''

    # Modify the contents
    fields = ['summary',
              'case_status',
              'category',
              'priority',
              'notes',
              'is_automated',
              'is_automated_proposed',
              'script',
              'arguments',
              'extra_link',
              'requirement',
              'alias']

    for field in fields:
        if getattr(tc, field) != tc_form.cleaned_data[field]:
            tc.log_action(request.user,
                          'Case %s changed from %s to %s in edit page.' % (
                              field, getattr(tc, field),
                              tc_form.cleaned_data[field]
                          ))
            setattr(tc, field, tc_form.cleaned_data[field])
    try:
        if tc.default_tester != tc_form.cleaned_data['default_tester']:
            tc.log_action(
                request.user,
                'Case default tester changed from %s to %s in edit page.' % (
                    tc.default_tester_id and tc.default_tester,
                    tc_form.cleaned_data['default_tester']
                ))
            tc.default_tester = tc_form.cleaned_data['default_tester']
    except ObjectDoesNotExist:
        pass
    tc.update_tags(tc_form.cleaned_data.get('tag'))
    try:
        fields_text = ['action', 'effect', 'setup', 'breakdown']
        latest_text = tc.latest_text()

        for field in fields_text:
            form_cleaned = tc_form.cleaned_data[field]
            if not (getattr(latest_text, field) or form_cleaned):
                continue
            if getattr(latest_text, field) != form_cleaned:
                tc.log_action(
                    request.user,
                    ' Case %s changed from %s to %s in edit page.' % (
                        field, getattr(latest_text, field) or None,
                        form_cleaned or None
                    ))
    except ObjectDoesNotExist:
        pass

    # FIXME: Bug here, timedelta from form cleaned data need to convert.
    tc.estimated_time = tc_form.cleaned_data['estimated_time']
    # IMPORTANT! tc.current_user is an instance attribute,
    # added so that in post_save, current logged-in user info
    # can be accessed.
    # Instance attribute is usually not a desirable solution.
    tc.current_user = request.user
    tc.save()


@permission_required('testcases.change_testcase')
def edit(request, case_id, template_name='case/edit.html'):
    """Edit case detail"""
    try:
        tc = TestCase.objects.select_related().get(case_id=case_id)
    except ObjectDoesNotExist:
        raise Http404

    tp = plan_from_request_or_none(request)

    if request.method == "POST":
        form = EditCaseForm(request.POST)
        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        elif tp:
            form.populate(product_id=tp.product_id)
        else:
            form.populate()

        n_form = CaseNotifyForm(request.POST)

        if form.is_valid() and n_form.is_valid():

            update_testcase(request, tc, form)

            tc.add_text(author=request.user,
                        action=form.cleaned_data['action'],
                        effect=form.cleaned_data['effect'],
                        setup=form.cleaned_data['setup'],
                        breakdown=form.cleaned_data['breakdown'])

            # Notification
            update_case_email_settings(tc, n_form)

            # Returns
            if request.POST.get('_continue'):
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('testcases-edit', args=[case_id, ]),
                    request.POST.get('from_plan', None),
                ))

            if request.POST.get('_continuenext'):
                if not tp:
                    raise Http404

                # find out test case list which belong to the same
                # classification
                confirm_status_name = 'CONFIRMED'
                if tc.case_status.name == confirm_status_name:
                    pk_list = tp.case.filter(
                        case_status__name=confirm_status_name)
                else:
                    pk_list = tp.case.exclude(
                        case_status__name=confirm_status_name)
                pk_list = list(pk_list.defer('case_id').values_list('pk', flat=True))
                pk_list.sort()

                # Get the previous and next case
                p_tc, n_tc = tc.get_previous_and_next(pk_list=pk_list)
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('testcases-edit', args=[n_tc.pk, ]),
                    tp.pk,
                ))

            if request.POST.get('_returntoplan'):
                if not tp:
                    raise Http404
                confirm_status_name = 'CONFIRMED'
                if tc.case_status.name == confirm_status_name:
                    return HttpResponseRedirect('%s#testcases' % (
                        reverse('test_plan_url_short', args=[tp.pk, ]),
                    ))
                else:
                    return HttpResponseRedirect('%s#reviewcases' % (
                        reverse('test_plan_url_short', args=[tp.pk, ]),
                    ))

            return HttpResponseRedirect('%s?from_plan=%s' % (
                reverse('testcases-get', args=[case_id, ]),
                request.POST.get('from_plan', None),
            ))

    else:
        tctxt = tc.latest_text()
        # Notification form initial
        n_form = CaseNotifyForm(initial={
            'notify_on_case_update': tc.emailing.notify_on_case_update,
            'notify_on_case_delete': tc.emailing.notify_on_case_delete,
            'author': tc.emailing.auto_to_case_author,
            'default_tester_of_case': tc.emailing.auto_to_case_tester,
            'managers_of_runs': tc.emailing.auto_to_run_manager,
            'default_testers_of_runs': tc.emailing.auto_to_run_tester,
            'assignees_of_case_runs': tc.emailing.auto_to_case_run_assignee,
            'cc_list': CC_LIST_DEFAULT_DELIMITER.join(
                tc.emailing.get_cc_list()),
        })
        default_tester = tc.default_tester_id and tc.default_tester.\
            email or None
        form = EditCaseForm(initial={
            'summary': tc.summary,
            'default_tester': default_tester,
            'requirement': tc.requirement,
            'is_automated': tc.get_is_automated_form_value(),
            'is_automated_proposed': tc.is_automated_proposed,
            'script': tc.script,
            'arguments': tc.arguments,
            'extra_link': tc.extra_link,
            'alias': tc.alias,
            'case_status': tc.case_status_id,
            'priority': tc.priority_id,
            'product': tc.category.product_id,
            'category': tc.category_id,
            'notes': tc.notes,
            'component': [c.pk for c in tc.component.all()],
            'estimated_time': tc.clear_estimated_time,
            'setup': tctxt.setup,
            'action': tctxt.action,
            'effect': tctxt.effect,
            'breakdown': tctxt.breakdown,
            'tag': ','.join(tc.tag.values_list('name', flat=True)),
        })

        form.populate(product_id=tc.category.product_id)

    context_data = {
        'test_case': tc,
        'test_plan': tp,
        'form': form,
        'notify_form': n_form,
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
    }
    return render(request, template_name, context_data)


def text_history(request, case_id, template_name='case/history.html'):
    """View test plan text history"""
    SUB_MODULE_NAME = 'cases'

    tc = get_object_or_404(TestCase, case_id=case_id)
    tp = plan_from_request_or_none(request)
    tctxts = tc.text.values('case_id',
                            'case_text_version',
                            'author__email',
                            'create_date').order_by('-case_text_version')

    context_data = {
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplan': tp,
        'testcase': tc,
        'test_case_texts': tctxts.iterator(),
    }

    try:
        case_text_version = int(request.GET.get('case_text_version'))
        text_to_show = tc.text.filter(case_text_version=case_text_version)
        text_to_show = text_to_show.values('action',
                                           'effect',
                                           'setup',
                                           'breakdown')

        context_data.update({
            'select_case_text_version': case_text_version,
            'text_to_show': text_to_show.iterator(),
        })
    except (TypeError, ValueError):
        # If case_text_version is not a valid number, no text to display for a
        # selected text history
        pass

    return render(request, template_name, context_data)


@permission_required('testcases.add_testcase')
def clone(request, template_name='case/clone.html'):
    """Clone one case or multiple case into other plan or plans"""
    SUB_MODULE_NAME = 'cases'

    request_data = getattr(request, request.method)

    if 'selectAll' not in request_data and 'case' not in request_data:
        return Prompt.render(
            request=request,
            info_type=Prompt.Info,
            info='At least one case is required.',
            next='javascript:window.history.go(-1)'
        )

    tp_src = plan_from_request_or_none(request)
    tp = None
    search_plan_form = SearchPlanForm()

    # Do the clone action
    if request.method == 'POST':
        clone_form = CloneCaseForm(request.POST)
        clone_form.populate(case_ids=request.POST.getlist('case'))

        if clone_form.is_valid():
            tcs_src = clone_form.cleaned_data['case']
            for tc_src in tcs_src:
                if clone_form.cleaned_data['copy_case']:
                    tc_dest = TestCase.objects.create(
                        is_automated=tc_src.is_automated,
                        is_automated_proposed=tc_src.is_automated_proposed,
                        script=tc_src.script,
                        arguments=tc_src.arguments,
                        extra_link=tc_src.extra_link,
                        summary=tc_src.summary,
                        requirement=tc_src.requirement,
                        alias=tc_src.alias,
                        estimated_time=tc_src.estimated_time,
                        case_status=TestCaseStatus.get_PROPOSED(),
                        category=tc_src.category,
                        priority=tc_src.priority,
                        notes=tc_src.notes,
                        author=clone_form.cleaned_data[
                            'maintain_case_orignal_author'] and
                        tc_src.author or request.user,
                        default_tester=clone_form.cleaned_data[
                            'maintain_case_orignal_default_tester'] and
                        tc_src.author or request.user,
                    )

                    for tp in clone_form.cleaned_data['plan']:
                        # copy a case and keep origin case's sortkey
                        if tp_src:
                            try:
                                tcp = TestCasePlan.objects.get(plan=tp_src,
                                                               case=tc_src)
                                sortkey = tcp.sortkey
                            except ObjectDoesNotExist:
                                sortkey = tp.get_case_sortkey()
                        else:
                            sortkey = tp.get_case_sortkey()

                        tp.add_case(tc_dest, sortkey)

                    tc_dest.add_text(
                        author=clone_form.cleaned_data[
                            'maintain_case_orignal_author'] and
                        tc_src.author or request.user,
                        create_date=tc_src.latest_text().create_date,
                        action=tc_src.latest_text().action,
                        effect=tc_src.latest_text().effect,
                        setup=tc_src.latest_text().setup,
                        breakdown=tc_src.latest_text().breakdown
                    )

                    for tag in tc_src.tag.all():
                        tc_dest.add_tag(tag=tag)

                    if clone_form.cleaned_data['copy_attachment']:
                        for attachment in tc_src.attachment.all():
                            TestCaseAttachment.objects.create(
                                case=tc_dest,
                                attachment=attachment,
                            )
                else:
                    tc_dest = tc_src
                    tc_dest.author = \
                        clone_form.cleaned_data[
                            'maintain_case_orignal_author'] \
                        and tc_src.author or request.user
                    tc_dest.default_tester = \
                        clone_form.cleaned_data[
                            'maintain_case_orignal_default_tester'] \
                        and tc_src.author or request.user
                    tc_dest.save()
                    for tp in clone_form.cleaned_data['plan']:
                        # create case link and keep origin plan's sortkey
                        if tp_src:
                            try:
                                tcp = TestCasePlan.objects.get(plan=tp_src,
                                                               case=tc_dest)
                                sortkey = tcp.sortkey
                            except ObjectDoesNotExist:
                                sortkey = tp.get_case_sortkey()
                        else:
                            sortkey = tp.get_case_sortkey()

                        try:
                            tp.add_case(tc_dest, sortkey)
                        except:
                            pass

                # Add the cases to plan
                for tp in clone_form.cleaned_data['plan']:
                    # Clone the categories to new product
                    if clone_form.cleaned_data['copy_case']:
                        try:
                            tc_category = tp.product.category.get(
                                name=tc_src.category.name
                            )
                        except ObjectDoesNotExist:
                            tc_category = tp.product.category.create(
                                name=tc_src.category.name,
                                description=tc_src.category.description,
                            )

                        tc_dest.category = tc_category
                        tc_dest.save()
                        del tc_category

                    # Clone the components to new product
                    if clone_form.cleaned_data['copy_component'] and \
                            clone_form.cleaned_data['copy_case']:
                        for component in tc_src.component.all():
                            try:
                                new_c = tp.product.component.get(
                                    name=component.name
                                )
                            except ObjectDoesNotExist:
                                new_c = tp.product.component.create(
                                    name=component.name,
                                    initial_owner=request.user,
                                    description=component.description,
                                )

                            try:
                                tc_dest.add_component(new_c)
                            except:
                                pass

            # Detect the number of items and redirect to correct one
            cases_count = len(clone_form.cleaned_data['case'])
            plans_count = len(clone_form.cleaned_data['plan'])

            if cases_count == 1 and plans_count == 1:
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('testcases-get', args=[tc_dest.pk, ]),
                    tp.pk
                ))

            if cases_count == 1:
                return HttpResponseRedirect(
                    reverse('testcases-get', args=[tc_dest.pk, ])
                )

            if plans_count == 1:
                return HttpResponseRedirect(
                    reverse('test_plan_url_short', args=[tp.pk, ])
                )

            # Otherwise it will prompt to user the clone action is successful.
            return Prompt.render(
                request=request,
                info_type=Prompt.Info,
                info='Test case successful to clone, click following link '
                     'to return to plans page.',
                next=reverse('plans-all')
            )
    else:
        selected_cases = get_selected_testcases(request)
        # Initial the clone case form
        clone_form = CloneCaseForm(initial={
            'case': selected_cases,
            'copy_case': False,
            'maintain_case_orignal_author': False,
            'maintain_case_orignal_default_tester': False,
            'copy_component': True,
            'copy_attachment': True,
        })
        clone_form.populate(case_ids=selected_cases)

    # Generate search plan form
    if request_data.get('from_plan'):
        tp = TestPlan.objects.get(plan_id=request_data['from_plan'])
        search_plan_form = SearchPlanForm(
            initial={'product': tp.product_id, 'is_active': True})
        search_plan_form.populate(product_id=tp.product_id)

    submit_action = request_data.get('submit', None)
    context_data = {
        'module': request_data.get('from_plan') and 'testplans' or MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'test_plan': tp,
        'search_form': search_plan_form,
        'clone_form': clone_form,
        'submit_action': submit_action,
    }
    return render(request, template_name, context_data)


@require_POST
def tag(request):
    """Remove tags from selected cases in plan page"""

    # FIXME: It's unnecessary to check existance of each case Id. Because, in
    # the following iteration through queried testcases, this problem is solved
    # naturally.
    tcs = get_selected_testcases(request)
    if not tcs:
        raise Http404

    # a == action
    if request.POST.get('a') == 'remove':
        tag_ids = request.POST.getlist('o_tag')
        tags = TestTag.objects.filter(pk__in=tag_ids)
        for tc in tcs:
            for tag in tags:
                try:
                    tc.remove_tag(tag=tag)
                except Exception as e:
                    return JsonResponse({
                        'rc': 1,
                        'response': str(e),
                        'errors_list': [{'case': tc.pk, 'tag': tag.pk}],
                    })
        return JsonResponse({'rc': 0, 'response': 'ok', 'errors_list': []})

    form = CaseTagForm(initial={'tag': request.POST.get('o_tag')})
    form.populate(case_ids=tcs)
    return HttpResponse(form.as_p())


@require_POST
@permission_required('testcases.add_testcasecomponent')
def component(request):
    """
    Management test case components
    """
    # FIXME: It will update product/category/component at one time so far.
    # We may disconnect the component from case product in future.
    cas = actions.ComponentActions(request)
    action = request.POST.get('a', 'render_form')
    func = getattr(cas, action.lower())
    return func()


@require_POST
@permission_required('testcases.add_testcasecomponent')
def category(request):
    """Management test case categories"""
    # FIXME: It will update product/category/component at one time so far.
    # We may disconnect the component from case product in future.
    cas = actions.CategoryActions(request)
    func = getattr(cas, request.POST.get('a', 'render_form').lower())
    return func()


@permission_required('testcases.add_testcaseattachment')
def attachment(request, case_id, template_name='case/attachment.html'):
    """Manage test case attachments"""
    SUB_MODULE_NAME = 'cases'

    file_size_limit = settings.MAX_UPLOAD_SIZE
    limit_readable = int(file_size_limit) / 2 ** 20  # Mb

    tc = get_object_or_404(TestCase, case_id=case_id)
    tp = plan_from_request_or_none(request)

    context_data = {
        'module': request.GET.get('from_plan') and 'testplans' or MODULE_NAME,
        'sub_module': SUB_MODULE_NAME,
        'testplan': tp,
        'testcase': tc,
        'limit': file_size_limit,
        'limit_readable': str(limit_readable) + "Mb",
    }
    return render(request, template_name, context_data)


def get_log(request, case_id, template_name="management/get_log.html"):
    """Get the case log"""
    tc = get_object_or_404(TestCase, case_id=case_id)

    context_data = {
        'object': tc
    }
    return render(request, template_name, context_data)


@permission_required('testcases.change_testcasebug')
def bug(request, case_id, template_name='case/get_bug.html'):
    """Process the bugs for cases"""
    # FIXME: Rewrite these codes for Ajax.Request
    tc = get_object_or_404(TestCase, case_id=case_id)

    class CaseBugActions(object):
        __all__ = ['get_form', 'render', 'add', 'remove']

        def __init__(self, request, case, template_name):
            self.request = request
            self.case = case
            self.template_name = template_name

        def render_form(self):
            form = CaseBugForm(initial={
                'case': self.case,
            })
            if request.GET.get('type') == 'table':
                return HttpResponse(form.as_table())

            return HttpResponse(form.as_p())

        def render(self, response=None):
            context_data = {
                'test_case': self.case,
                'response': response
            }
            return render(request, template_name, context_data)

        def add(self):
            # FIXME: It's may use ModelForm.save() method here.
            #        Maybe in future.
            if not self.request.user.has_perm('testcases.add_testcasebug'):
                return self.render(response='Permission denied.')

            form = CaseBugForm(request.GET)
            if not form.is_valid():
                errors = []
                for field_name, messages in form.errors.iteritems():
                    for item in messages:
                        errors.append(item)
                response = '\n'.join(errors)
                return self.render(response=response)

            try:
                self.case.add_bug(
                    bug_id=form.cleaned_data['bug_id'],
                    bug_system_id=form.cleaned_data['bug_system'].pk,
                    summary=form.cleaned_data['summary'],
                    description=form.cleaned_data['description'],
                )
            except Exception as e:
                return self.render(response=str(e))

            return self.render()

        def remove(self):
            if not request.user.has_perm('testcases.delete_testcasebug'):
                return self.render(response='Permission denied.')

            try:
                self.case.remove_bug(request.GET.get('id'), request.GET.get('run_id'))
            except ObjectDoesNotExist, error:
                return self.render(response=error)

            return self.render()

    case_bug_actions = CaseBugActions(
        request=request,
        case=tc,
        template_name=template_name
    )

    if not request.GET.get('handle') in case_bug_actions.__all__:
        return case_bug_actions.render(response='Unrecognizable actions')

    func = getattr(case_bug_actions, request.GET['handle'])
    return func()


@require_GET
def plan(request, case_id):
    """Add and remove plan in plan tab"""
    tc = get_object_or_404(TestCase, case_id=case_id)
    if request.GET.get('a'):
        # Search the plans from database
        if not request.GET.getlist('plan_id'):
            context_data = {
                'message': 'The case must specific one plan at leaset for '
                           'some action',
            }
            return render(
                request,
                'case/get_plan.html',
                context_data)

        tps = TestPlan.objects.filter(pk__in=request.GET.getlist('plan_id'))

        if not tps:
            context_data = {
                'testplans': tps,
                'message': 'The plan id are not exist in database at all.'
            }
            return render(
                request,
                'case/get_plan.html',
                context_data)

        # Add case plan action
        if request.GET['a'] == 'add':
            if not request.user.has_perm('testcases.add_testcaseplan'):
                context_data = {
                    'test_case': tc,
                    'test_plans': tps,
                    'message': 'Permission denied',
                }
                return render(
                    request,
                    'case/get_plan.html',
                    context_data)

            for tp in tps:
                tc.add_to_plan(tp)

        # Remove case plan action
        if request.GET['a'] == 'remove':
            if not request.user.has_perm('testcases.change_testcaseplan'):
                context_data = {
                    'test_case': tc,
                    'test_plans': tps,
                    'message': 'Permission denied',
                }
                return render(
                    request,
                    'case/get_plan.html',
                    context_data)

            for tp in tps:
                tc.remove_plan(tp)

    tps = tc.plan.all()
    tps = tps.select_related('author',
                             'type',
                             'product')

    context_data = {
        'test_case': tc,
        'test_plans': tps,
    }
    return render(
        request,
        'case/get_plan.html',
        context_data)
