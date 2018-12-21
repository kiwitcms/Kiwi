# -*- coding: utf-8 -*-

import itertools

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db.models import Count
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView

from django_comments.models import Comment

from tcms.core.contrib.comments.utils import get_comments
from tcms.search import remove_from_request_path
from tcms.search.order import order_case_queryset
from tcms.testcases.models import TestCase, TestCaseStatus, \
    TestCasePlan, BugSystem, TestCaseText
from tcms.management.models import Priority, Tag
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestCaseRun
from tcms.testruns.models import TestCaseRunStatus
from tcms.testcases.forms import NewCaseForm, \
    SearchCaseForm, EditCaseForm, CaseNotifyForm, \
    CloneCaseForm, CaseBugForm
from tcms.testplans.forms import SearchPlanForm
from tcms.utils.dict_utils import create_dict_from_query
from tcms.testcases.fields import MultipleEmailField


TESTCASE_OPERATION_ACTIONS = (
    'search', 'sort', 'update',
    'remove',  # including remove tag from cases
    'add',  # including add tag to cases
    'change',
    'delete_cases',  # unlink cases from a TestPlan
)


# _____________________________________________________________________________
# helper functions


def plan_from_request_or_none(request):
    """Get TestPlan from REQUEST

    This method relies on the existence of from_plan within REQUEST.
    """
    test_plan_id = request.POST.get("from_plan") or request.GET.get("from_plan")
    if not test_plan_id:
        return None
    return get_object_or_404(TestPlan, plan_id=test_plan_id)


def update_case_email_settings(test_case, n_form):
    """Update testcase's email settings."""

    test_case.emailing.notify_on_case_update = n_form.cleaned_data[
        'notify_on_case_update']
    test_case.emailing.notify_on_case_delete = n_form.cleaned_data[
        'notify_on_case_delete']
    test_case.emailing.auto_to_case_author = n_form.cleaned_data[
        'author']
    test_case.emailing.auto_to_case_tester = n_form.cleaned_data[
        'default_tester_of_case']
    test_case.emailing.auto_to_run_manager = n_form.cleaned_data[
        'managers_of_runs']
    test_case.emailing.auto_to_run_tester = n_form.cleaned_data[
        'default_testers_of_runs']
    test_case.emailing.auto_to_case_run_assignee = n_form.cleaned_data[
        'assignees_of_case_runs']

    default_tester = n_form.cleaned_data['default_tester_of_case']
    if (default_tester and test_case.default_tester_id):
        test_case.emailing.auto_to_case_tester = True

    # Continue to update CC list
    valid_emails = n_form.cleaned_data['cc_list']
    test_case.emailing.cc_list = MultipleEmailField.delimiter.join(valid_emails)

    test_case.emailing.save()


def group_case_bugs(bugs):
    """Group bugs using bug_id."""
    grouped_bugs = []

    for _pk, _bugs in itertools.groupby(bugs, lambda b: b.bug_id):
        grouped_bugs.append((_pk, list(_bugs)))

    return grouped_bugs


def create_testcase(request, form, test_plan):
    """Create testcase"""
    test_case = TestCase.create(author=request.user, values=form.cleaned_data)
    test_case.add_text(case_text_version=1,
                       author=request.user,
                       action=form.cleaned_data['action'],
                       effect=form.cleaned_data['effect'],
                       setup=form.cleaned_data['setup'],
                       breakdown=form.cleaned_data['breakdown'])

    # Assign the case to the plan
    if test_plan:
        test_case.add_to_plan(plan=test_plan)

    # Add components into the case
    for component in form.cleaned_data['component']:
        test_case.add_component(component=component)
    return test_case


class ReturnActions:
    all_actions = ('_addanother', '_continue', 'returntocase', '_returntoplan')

    def __init__(self, case, plan, default_form_parameters):
        self.case = case
        self.plan = plan
        self.default_form_parameters = default_form_parameters

    def _continue(self):
        if self.plan:
            return HttpResponseRedirect(
                '%s?from_plan=%s' % (reverse('testcases-edit',
                                             args=[self.case.case_id]),
                                     self.plan.plan_id))

        return HttpResponseRedirect(
            reverse('testcases-edit', args=[self.case.case_id]))

    def _addanother(self):
        form = NewCaseForm(initial=self.default_form_parameters)

        if self.plan:
            form.populate(product_id=self.plan.product_id)

        return form

    def returntocase(self):
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


@permission_required('testcases.add_testcase')
def new(request, template_name='case/edit.html'):
    """New testcase"""
    test_plan = plan_from_request_or_none(request)
    # Initial the form parameters when write new case from plan
    if test_plan:
        default_form_parameters = {
            'product': test_plan.product_id,
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
            test_case = create_testcase(request, form, test_plan)
            # Generate the instance of actions
            ras = ReturnActions(test_case, test_plan, default_form_parameters)
            for ra_str in ras.all_actions:
                if request.POST.get(ra_str):
                    func = getattr(ras, ra_str)
                    break
            else:
                func = ras.returntocase

            # Get the function and return back
            result = func()
            if isinstance(result, HttpResponseRedirect):
                return result
            # Assume here is the form
            form = result

    # Initial NewCaseForm for submit
    else:
        test_plan = plan_from_request_or_none(request)
        form = NewCaseForm(initial=default_form_parameters)
        if test_plan:
            form.populate(product_id=test_plan.product_id)

    context_data = {
        'test_plan': test_plan,
        'form': form
    }
    return render(request, template_name, context_data)


def get_testcaseplan_sortkey_pk_for_testcases(plan, tc_ids):
    """Get each TestCase' sortkey and related TestCasePlan's pk"""
    qs = TestCasePlan.objects.filter(case__in=tc_ids)
    if plan is not None:
        qs = qs.filter(plan__pk=plan.pk)
    qs = qs.values('pk', 'sortkey', 'case')
    return dict([(item['case'], {
        'testcaseplan_pk': item['pk'],
        'sortkey': item['sortkey']
    }) for item in qs])


def calculate_for_testcases(plan, testcases):
    """Calculate extra data for TestCases

    Attach TestCasePlan.sortkey, TestCasePlan.pk, and the number of bugs of
    each TestCase.

    Arguments:
    - plan: the TestPlan containing searched TestCases. None means testcases
      are not limited to a specific TestPlan.
    - testcases: a queryset of TestCases.
    """
    tc_ids = []
    for test_case in testcases:
        tc_ids.append(test_case.pk)

    sortkey_tcpkan_pks = get_testcaseplan_sortkey_pk_for_testcases(
        plan, tc_ids)

    for test_case in testcases:
        data = sortkey_tcpkan_pks.get(test_case.pk, None)
        if data:
            # todo: these properties appear to be redundant since the same
            # info should be available from the test_case query
            setattr(test_case, 'cal_sortkey', data['sortkey'])
            setattr(test_case, 'cal_testcaseplan_pk', data['testcaseplan_pk'])
        else:
            setattr(test_case, 'cal_sortkey', None)
            setattr(test_case, 'cal_testcaseplan_pk', None)

    return testcases


def get_case_status(template_type):
    """Get part or all TestCaseStatus according to template type"""
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
    """Build search form preparing for quering TestCases"""
    # Initial the form and template
    action = request.POST.get('a')
    if action in TESTCASE_OPERATION_ACTIONS:
        search_form = SearchCaseForm(request.POST)
        request.session['items_per_page'] = \
            request.POST.get('items_per_page', settings.DEFAULT_PAGE_SIZE)
    else:
        d_status = get_case_status(request.POST.get('template_type'))
        d_status_ids = d_status.values_list('pk', flat=True)
        items_per_page = request.session.get('items_per_page',
                                             settings.DEFAULT_PAGE_SIZE)
        search_form = SearchCaseForm(initial={
            'case_status': d_status_ids,
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
    """Paginate queried TestCases

    Arguments:
    - request: django's HttpRequest from which to get pagination data
    - testcases: an object queryset representing already queried TestCases

    Return value: return the queryset for chain call
    """

    page_index = int(request.POST.get('page_index', 1))
    page_size = int(request.POST.get(
        'items_per_page',
        request.session.get(
            'items_per_page', settings.DEFAULT_PAGE_SIZE
        )
    ))
    offset = (page_index - 1) * page_size
    return testcases[offset:offset + page_size]


def sort_queried_testcases(request, testcases):
    """Sort querid TestCases according to sort key

    Arguments:
    - request: REQUEST object
    - testcases: object of QuerySet containing queried TestCases
    """
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
    """Query TestCases according to criterias coming within REQUEST

    Arguments:
    - request: the REQUEST object.
    - plan: instance of TestPlan to restrict only those TestCases belongs to
      the TestPlan. Can be None. As you know, query from all TestCases.
    """
    search_form = build_cases_search_form(request)

    action = request.POST.get('a')
    if action == 'initial':
        # todo: build_cases_search_form will also check TESTCASE_OPERATION_ACTIONS
        # and return slightly different values in case of initialization
        # move the check there and just execute the query here if the data
        # is valid
        d_status = get_case_status(request.POST.get('template_type'))
        tcs = TestCase.objects.filter(case_status__in=d_status)
    elif action in TESTCASE_OPERATION_ACTIONS and search_form.is_valid():
        tcs = TestCase.list(search_form.cleaned_data, plan)
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
    return tcs, search_form


def get_selected_testcases(request):
    """Get selected TestCases from client side

    TestCases are selected in two cases. One is user selects part of displayed
    TestCases, where there should be at least one variable named case, whose
    value is the TestCase Id. Another one is user selects all TestCases based
    on previous filter criterias even through there are non-displayed ones. In
    this case, another variable selectAll appears in the REQUEST. Whatever its
    value is.

    If neither variables mentioned exists, empty query result is returned.

    Arguments:
    - request: REQUEST object.
    """
    method = request.POST or request.GET
    if method.get('selectAll', None):
        plan = plan_from_request_or_none(request)
        cases, _search_form = query_testcases_from_request(request, plan)
        return cases

    return TestCase.objects.filter(pk__in=method.getlist('case'))


def load_more_cases(request, template_name='plan/cases_rows.html'):
    """Loading more TestCases"""
    plan = plan_from_request_or_none(request)
    cases = []
    selected_case_ids = []
    if plan is not None:
        cases, _search_form = query_testcases_from_request(request, plan)
        cases = sort_queried_testcases(request, cases)
        cases = paginate_testcases(request, cases)
        cases = calculate_for_testcases(plan, cases)
        selected_case_ids = []
        for test_case in cases:
            selected_case_ids.append(test_case.pk)
    context_data = {
        'test_plan': plan,
        'test_cases': cases,
        'selected_case_ids': selected_case_ids,
        'case_status': TestCaseStatus.objects.all(),
    }
    return render(request, template_name, context_data)


def get_tags_from_cases(case_ids, plan=None):
    """Get all tags from test cases

    @param cases: an iterable object containing test cases' ids
    @type cases: list, tuple

    @param plan: TestPlan object

    @return: a list containing all found tags with id and name
    @rtype: list
    """
    query = Tag.objects.filter(case__in=case_ids).distinct().order_by('name')
    if plan:
        query = query.filter(case__plan=plan)

    return query


@require_POST
def list_all(request):
    """
    Generate the TestCase list for the UI tabs in TestPlan page view.

    POST Parameters:
    from_plan: Plan ID
       -- [number]: When the plan ID defined, it will build the case
    page in plan.

    """
    # Intial the plan in plan details page
    test_plan = plan_from_request_or_none(request)
    if not test_plan:
        messages.add_message(request,
                             messages.ERROR,
                             _('TestPlan not specified or does not exist'))
        return HttpResponseRedirect(reverse('core-views-index'))

    tcs, search_form = query_testcases_from_request(request, test_plan)
    tcs = sort_queried_testcases(request, tcs)
    total_cases_count = tcs.count()

    # Get the tags own by the cases
    ttags = get_tags_from_cases((case.pk for case in tcs), test_plan)

    tcs = paginate_testcases(request, tcs)

    # There are several extra information related to each TestCase to be shown
    # also. This step must be the very final one, because the calculation of
    # related data requires related TestCases' IDs, that is the queryset of
    # TestCases should be evaluated in advance.
    tcs = calculate_for_testcases(test_plan, tcs)

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

    selected_case_ids = []
    for test_case in get_selected_testcases(request):
        selected_case_ids.append(test_case.pk)

    context_data = {
        'test_cases': tcs,
        'test_plan': test_plan,
        'search_form': search_form,
        # selected_case_ids is used in template to decide whether or not this TestCase is selected
        'selected_case_ids': selected_case_ids,
        'case_status': TestCaseStatus.objects.all(),
        'priorities': Priority.objects.filter(is_active=True),
        'case_own_tags': ttags,
        'query_url': query_url,

        # Load more is a POST request, so POST parameters are required only.
        # Remember this for loading more cases with the same as criterias.
        'search_criterias': request.body.decode(),
        'total_cases_count': total_cases_count,
    }
    return render(request, 'plan/get_cases.html', context_data)


@require_GET
def search(request):
    """
        Shows the search form which uses JSON RPC to fetch the resuts
    """
    form = SearchCaseForm(request.GET)
    if request.GET.get('product'):
        form.populate(product_id=request.GET['product'])
    else:
        form.populate()

    context_data = {
        'form': form,
    }
    return render(request, 'testcases/search.html', context_data)


class SimpleTestCaseView(TemplateView):
    """Simple read-only TestCase View used in TestPlan page"""

    template_name = 'case/get_details.html'
    review_mode = None

    def get(self, request, *args, **kwargs):
        self.review_mode = request.GET.get('review_mode')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        case = TestCase.objects.get(pk=kwargs['case_id'])
        data.update({
            'test_case': case,
            'review_mode': self.review_mode,
            'test_case_text': case.latest_text(),
            'components': case.component.only('name'),
            'tags': case.tag.only('name'),
            'case_comments': get_comments(case),
        })

        return data


def get_comments_count(caserun_ids):
    content_type = ContentType.objects.get_for_model(TestCaseRun)
    comments = Comment.objects.filter(content_type=content_type,
                                      object_pk__in=caserun_ids,
                                      site_id=settings.SITE_ID,
                                      is_removed=False)
    comments = comments.values('object_pk').annotate(comment_count=Count('pk'))
    result = {}
    for item in comments.iterator():
        result[int(item['object_pk'])] = item['comment_count']
    return result


class TestCaseCaseRunListPaneView(TemplateView):
    """Display case runs list when expand a plan item from case page, Case Runs tab"""

    template_name = 'case/get_case_runs_by_plan.html'
    plan_id = None

    def get(self, request, *args, **kwargs):
        plan_id = self.request.GET.get('plan_id', None)
        self.plan_id = int(plan_id) if plan_id is not None else None
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        case_runs = TestCaseRun.objects.filter(
            case=kwargs['case_id'],
            run__plan=self.plan_id
        ).values(
            'pk', 'case_id', 'run_id', 'case_text_version',
            'close_date', 'sortkey',
            'tested_by__username', 'assignee__username',
            'run__plan_id', 'run__summary',
            'case__category__name', 'case__priority__value',
            'case_run_status__name',
        ).order_by('pk')

        # Get the number of each caserun's comments, and put the count into
        # comments query result.
        caserun_ids = []

        for item in case_runs:
            caserun_ids.append(item['pk'])

        comments_count = get_comments_count(caserun_ids)
        for case_run in case_runs:
            case_run['comments_count'] = comments_count.get(case_run['pk'], 0)

        data.update({
            'case_runs': case_runs,
        })
        return data


class TestCaseSimpleCaseRunView(TemplateView):
    """Display caserun information in Case Runs tab in case page

    This view only shows notes, comments and logs simply. So, call it simple.
    """

    template_name = 'case/get_details_case_case_run.html'
    caserun_id = None

    def get(self, request, *args, **kwargs):
        try:
            self.caserun_id = int(request.GET.get('case_run_id', None))
        except (TypeError, ValueError):
            raise Http404

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        caserun = TestCaseRun.objects.get(pk=self.caserun_id)
        comments = get_comments(caserun)

        data.update({
            'test_caserun': caserun,
            'comments': comments.iterator(),
        })
        return data


class TestCaseCaseRunDetailPanelView(TemplateView):
    """Display case run detail in run page"""

    template_name = 'case/get_details_case_run.html'
    caserun_id = None
    case_text_version = None

    def get(self, request, *args, **kwargs):
        try:
            self.caserun_id = int(request.GET.get('case_run_id'))
            self.case_text_version = int(request.GET.get('case_text_version'))
        except (TypeError, ValueError):
            raise Http404

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        case = TestCase.objects.get(pk=kwargs['case_id'])
        case_run = TestCaseRun.objects.get(pk=self.caserun_id)

        # Data of TestCase
        test_case_text = case.get_text_with_version(self.case_text_version)

        # Data of TestCaseRun
        caserun_comments = get_comments(case_run)

        caserun_status = TestCaseRunStatus.objects.values('pk', 'name')
        caserun_status = caserun_status.order_by('pk')
        bugs = group_case_bugs(case_run.case.get_bugs().order_by('bug_id'))

        data.update({
            'test_case': case,
            'test_case_text': test_case_text,

            'test_case_run': case_run,
            'comments_count': len(caserun_comments),
            'caserun_comments': caserun_comments,
            'caserun_logs': case_run.history.all(),
            'test_case_run_status': caserun_status,
            'grouped_case_bugs': bugs,
        })

        return data


def get(request, case_id):
    """Get the case content"""
    # Get the case
    try:
        test_case = TestCase.objects.select_related(
            'author', 'default_tester',
            'category', 'category',
            'priority', 'case_status').get(case_id=case_id)
    except ObjectDoesNotExist:
        raise Http404

    # Get the test plans
    tps = test_case.plan.select_related('author', 'product', 'type').all()

    try:
        test_plan = tps.get(pk=request.GET.get('from_plan', 0))
    except (TestPlan.DoesNotExist, ValueError):
        # ValueError is raised when from_plan is empty string
        # not viewing TC from a Plan or specified Plan does not exist (e.g. broken link)
        test_plan = None

    # Get the test case runs
    tcrs = test_case.case_run.select_related(
        'run', 'tested_by',
        'assignee', 'case',
        'case', 'case_run_status').order_by('run__plan')
    # FIXME: Just don't know why Django template does not evaluate a generator,
    # and had to evaluate the groupby generator manually like below.
    runs_ordered_by_plan = []
    for key, value in itertools.groupby(tcrs, lambda t: t.run.plan):
        runs_ordered_by_plan.append((key, list(value)))

    case_run_plans = []
    for key, _value in runs_ordered_by_plan:
        case_run_plans.append(key)

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
    tc_text = test_case.get_text_with_version(request.GET.get('case_text_version'))

    grouped_case_bugs = tcr and group_case_bugs(tcr.case.get_bugs())
    # Render the page
    context_data = {
        'test_case': test_case,
        'test_plan': test_plan,
        'test_plans': tps,
        'test_case_runs': tcrs,
        'case_run_plans': case_run_plans,
        'test_case_runs_by_plan': case_runs_by_plan,
        'test_case_run': tcr,
        'grouped_case_bugs': grouped_case_bugs,
        'test_case_text': tc_text,
        'test_case_status': TestCaseStatus.objects.all(),
        'test_case_run_status': TestCaseRunStatus.objects.all(),
        'bug_trackers': BugSystem.objects.all(),
    }
    return render(request, 'case/get.html', context_data)


@require_POST
def printable(request, template_name='case/printable.html'):
    """
        Create the printable copy for plan/case.
        Only CONFIRMED TestCases are printed when printing a TestPlan!
    """
    # fixme: remove when TestPlan and TestCase templates have been converted to Patternfly
    # instead of generating the print values on the backend we can use CSS to do
    # this in the browser
    # search only by case PK. Used when printing selected cases
    case_ids = request.POST.getlist('case')
    case_filter = {'case__in': case_ids}

    test_plan = None
    # plan_pk is passed from the TestPlan.printable function
    # but it doesn't pass IDs of individual cases to be printed
    if not case_ids:
        plan_pk = request.POST.get('plan', 0)
        try:
            test_plan = TestPlan.objects.get(pk=plan_pk)
            # search cases from a TestPlan, used when printing entire plan
            case_filter = {
                'case__in': test_plan.case.all(),
                'case__case_status': TestCaseStatus.objects.get(name='CONFIRMED').pk,
            }
        except (ValueError, TestPlan.DoesNotExist):
            test_plan = None

    tcs = create_dict_from_query(
        TestCaseText.objects.filter(**case_filter).values(
            'case_id', 'case__summary', 'setup', 'action', 'effect', 'breakdown'
        ).order_by('case_id', '-case_text_version'),
        'case_id',
        True
    )

    context_data = {
        'test_plan': test_plan,
        'test_cases': tcs,
    }
    return render(request, template_name, context_data)


def update_testcase(request, test_case, tc_form):
    """Updating information of specific TestCase

    This is called by views.edit internally. Don't call this directly.

    Arguments:
    - test_case: instance of a TestCase being updated
    - tc_form: instance of django.forms.Form, holding validated data.
    """

    # TODO: this entire function doesn't seem very useful
    # part if it was logging the changes but now this is
    # done by simple_history. Should we remove it ???
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
        if getattr(test_case, field) != tc_form.cleaned_data[field]:
            setattr(test_case, field, tc_form.cleaned_data[field])
    try:
        if test_case.default_tester != tc_form.cleaned_data['default_tester']:
            test_case.default_tester = tc_form.cleaned_data['default_tester']
    except ObjectDoesNotExist:
        pass

    # IMPORTANT! test_case.current_user is an instance attribute,
    # added so that in post_save, current logged-in user info
    # can be accessed.
    # Instance attribute is usually not a desirable solution.
    # TODO: current_user is probbably not necessary now that we have proper history
    # it is used in email templates though !!!
    test_case.current_user = request.user
    test_case.save()


@permission_required('testcases.change_testcase')
def edit(request, case_id, template_name='case/edit.html'):
    """Edit case detail"""
    try:
        test_case = TestCase.objects.select_related().get(case_id=case_id)
    except ObjectDoesNotExist:
        raise Http404

    test_plan = plan_from_request_or_none(request)

    if request.method == "POST":
        form = EditCaseForm(request.POST)
        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        elif test_plan:
            form.populate(product_id=test_plan.product_id)
        else:
            form.populate()

        n_form = CaseNotifyForm(request.POST)

        if form.is_valid() and n_form.is_valid():

            update_testcase(request, test_case, form)

            test_case.add_text(author=request.user,
                               action=form.cleaned_data['action'],
                               effect=form.cleaned_data['effect'],
                               setup=form.cleaned_data['setup'],
                               breakdown=form.cleaned_data['breakdown'])

            # Notification
            update_case_email_settings(test_case, n_form)

            # Returns
            if request.POST.get('_continue'):
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('testcases-edit', args=[case_id, ]),
                    request.POST.get('from_plan', None),
                ))

            if request.POST.get('_continuenext'):
                if not test_plan:
                    raise Http404

                # find out test case list which belong to the same
                # classification
                confirm_status_name = 'CONFIRMED'
                if test_case.case_status.name == confirm_status_name:
                    pk_list = test_plan.case.filter(
                        case_status__name=confirm_status_name)
                else:
                    pk_list = test_plan.case.exclude(
                        case_status__name=confirm_status_name)
                pk_list = list(pk_list.defer('case_id').values_list('pk', flat=True))
                pk_list.sort()

                # Get the next case
                _prev_case, next_case = test_case.get_previous_and_next(pk_list=pk_list)
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('testcases-edit', args=[next_case.pk, ]),
                    test_plan.pk,
                ))

            if request.POST.get('_returntoplan'):
                if not test_plan:
                    raise Http404
                confirm_status_name = 'CONFIRMED'
                if test_case.case_status.name == confirm_status_name:
                    return HttpResponseRedirect('%s#testcases' % (
                        reverse('test_plan_url_short', args=[test_plan.pk, ]),
                    ))
                return HttpResponseRedirect('%s#reviewcases' % (
                    reverse('test_plan_url_short', args=[test_plan.pk, ]),
                ))

            return HttpResponseRedirect('%s?from_plan=%s' % (
                reverse('testcases-get', args=[case_id, ]),
                request.POST.get('from_plan', None),
            ))

    else:
        tctxt = test_case.latest_text()
        # Notification form initial
        n_form = CaseNotifyForm(initial={
            'notify_on_case_update': test_case.emailing.notify_on_case_update,
            'notify_on_case_delete': test_case.emailing.notify_on_case_delete,
            'author': test_case.emailing.auto_to_case_author,
            'default_tester_of_case': test_case.emailing.auto_to_case_tester,
            'managers_of_runs': test_case.emailing.auto_to_run_manager,
            'default_testers_of_runs': test_case.emailing.auto_to_run_tester,
            'assignees_of_case_runs': test_case.emailing.auto_to_case_run_assignee,
            'cc_list': MultipleEmailField.delimiter.join(
                test_case.emailing.get_cc_list()),
        })

        components = []
        for component in test_case.component.all():
            components.append(component.pk)

        default_tester = None
        if test_case.default_tester_id:
            default_tester = test_case.default_tester.email

        form = EditCaseForm(initial={
            'summary': test_case.summary,
            'default_tester': default_tester,
            'requirement': test_case.requirement,
            'is_automated': test_case.get_is_automated_form_value(),
            'is_automated_proposed': test_case.is_automated_proposed,
            'script': test_case.script,
            'arguments': test_case.arguments,
            'extra_link': test_case.extra_link,
            'alias': test_case.alias,
            'case_status': test_case.case_status_id,
            'priority': test_case.priority_id,
            'product': test_case.category.product_id,
            'category': test_case.category_id,
            'notes': test_case.notes,
            'component': components,
            'setup': tctxt.setup,
            'action': tctxt.action,
            'effect': tctxt.effect,
            'breakdown': tctxt.breakdown,
        })

        form.populate(product_id=test_case.category.product_id)

    context_data = {
        'test_case': test_case,
        'test_plan': test_plan,
        'form': form,
        'notify_form': n_form,
    }
    return render(request, template_name, context_data)


def text_history(request, case_id, template_name='case/history.html'):
    """View test plan text history"""

    test_case = get_object_or_404(TestCase, case_id=case_id)
    test_plan = plan_from_request_or_none(request)
    tctxts = test_case.text.values('case_id',
                                   'case_text_version',
                                   'author__email',
                                   'create_date').order_by('-case_text_version')

    context = {
        'testplan': test_plan,
        'testcase': test_case,
        'test_case_texts': tctxts.iterator(),
    }

    try:
        case_text_version = int(request.GET.get('case_text_version'))
        text_to_show = test_case.text.filter(case_text_version=case_text_version)
        text_to_show = text_to_show.values('action',
                                           'effect',
                                           'setup',
                                           'breakdown')

        context.update({
            'select_case_text_version': case_text_version,
            'text_to_show': text_to_show.iterator(),
        })
    except (TypeError, ValueError):
        # If case_text_version is not a valid number, no text to display for a
        # selected text history
        pass

    return render(request, template_name, context)


@permission_required('testcases.add_testcase')
def clone(request, template_name='case/clone.html'):
    """Clone one case or multiple case into other plan or plans"""

    request_data = getattr(request, request.method)

    if 'selectAll' not in request_data and 'case' not in request_data:
        messages.add_message(request,
                             messages.ERROR,
                             _('At least one TestCase is required'))
        # redirect back where we came from
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    test_plan_src = plan_from_request_or_none(request)
    test_plan = None
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
                        case_status=TestCaseStatus.get_proposed(),
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

                    for test_plan in clone_form.cleaned_data['plan']:
                        # copy a case and keep origin case's sortkey
                        if test_plan_src:
                            try:
                                tcp = TestCasePlan.objects.get(plan=test_plan_src,
                                                               case=tc_src)
                                sortkey = tcp.sortkey
                            except ObjectDoesNotExist:
                                sortkey = test_plan.get_case_sortkey()
                        else:
                            sortkey = test_plan.get_case_sortkey()

                        test_plan.add_case(tc_dest, sortkey)

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
                else:
                    tc_dest = tc_src
                    tc_dest.author = request.user
                    if clone_form.cleaned_data['maintain_case_orignal_author']:
                        tc_dest.author = tc_src.author

                    tc_dest.default_tester = request.user
                    if clone_form.cleaned_data['maintain_case_orignal_default_tester']:
                        tc_dest.default_tester = tc_src.default_tester

                    tc_dest.save()

                    for test_plan in clone_form.cleaned_data['plan']:
                        # create case link and keep origin plan's sortkey
                        if test_plan_src:
                            try:
                                tcp = TestCasePlan.objects.get(plan=test_plan_src,
                                                               case=tc_dest)
                                sortkey = tcp.sortkey
                            except ObjectDoesNotExist:
                                sortkey = test_plan.get_case_sortkey()
                        else:
                            sortkey = test_plan.get_case_sortkey()

                        test_plan.add_case(tc_dest, sortkey)

                # Add the cases to plan
                for test_plan in clone_form.cleaned_data['plan']:
                    # Clone the categories to new product
                    if clone_form.cleaned_data['copy_case']:
                        try:
                            tc_category = test_plan.product.category.get(
                                name=tc_src.category.name
                            )
                        except ObjectDoesNotExist:
                            tc_category = test_plan.product.category.create(
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
                                new_c = test_plan.product.component.get(
                                    name=component.name
                                )
                            except ObjectDoesNotExist:
                                new_c = test_plan.product.component.create(
                                    name=component.name,
                                    initial_owner=request.user,
                                    description=component.description,
                                )

                            tc_dest.add_component(new_c)

            # Detect the number of items and redirect to correct one
            cases_count = len(clone_form.cleaned_data['case'])
            plans_count = len(clone_form.cleaned_data['plan'])

            if cases_count == 1 and plans_count == 1:
                return HttpResponseRedirect('%s?from_plan=%s' % (
                    reverse('testcases-get', args=[tc_dest.pk, ]),
                    test_plan.pk
                ))

            if cases_count == 1:
                return HttpResponseRedirect(
                    reverse('testcases-get', args=[tc_dest.pk, ])
                )

            if plans_count == 1:
                return HttpResponseRedirect(
                    reverse('test_plan_url_short', args=[test_plan.pk, ])
                )

            # Otherwise it will prompt to user the clone action is successful.
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('TestCase cloning was successful'))
            return HttpResponseRedirect(reverse('plans-search'))
    else:
        selected_cases = get_selected_testcases(request)
        # Initial the clone case form
        clone_form = CloneCaseForm(initial={
            'case': selected_cases,
            'copy_case': False,
            'maintain_case_orignal_author': False,
            'maintain_case_orignal_default_tester': False,
            'copy_component': True,
        })
        clone_form.populate(case_ids=selected_cases)

    # Generate search plan form
    if request_data.get('from_plan'):
        test_plan = TestPlan.objects.get(plan_id=request_data['from_plan'])
        search_plan_form = SearchPlanForm(
            initial={'product': test_plan.product_id, 'is_active': True})
        search_plan_form.populate(product_id=test_plan.product_id)

    submit_action = request_data.get('submit', None)
    context = {
        'test_plan': test_plan,
        'search_form': search_plan_form,
        'clone_form': clone_form,
        'submit_action': submit_action,
    }
    return render(request, template_name, context)


@permission_required('testcases.add_testcaseattachment')
def attachment(request, case_id, template_name='case/attachment.html'):
    """Manage test case attachments"""

    test_case = get_object_or_404(TestCase, case_id=case_id)
    test_plan = plan_from_request_or_none(request)

    context = {
        'testplan': test_plan,
        'testcase': test_case,
        'limit': settings.FILE_UPLOAD_MAX_SIZE,
    }
    return render(request, template_name, context)


@permission_required('testcases.change_bug')
def bug(request, case_id, template_name='case/get_bug.html'):
    """Process the bugs for cases"""
    # FIXME: Rewrite these codes for Ajax.Request
    test_case = get_object_or_404(TestCase, case_id=case_id)

    class CaseBugActions:
        all_actions = ['get_form', 'render', 'add']

        def __init__(self, request, case, template_name):
            self.request = request
            self.case = case
            self.template_name = template_name

        def render(self, response=None):
            context = {
                'test_case': self.case,
                'response': response
            }
            return render(request, template_name, context)

        def add(self):
            # FIXME: It's may use ModelForm.save() method here.
            #        Maybe in future.
            if not self.request.user.has_perm('testcases.add_bug'):
                return self.render(response='Permission denied.')

            form = CaseBugForm(request.GET)
            if not form.is_valid():
                errors = []
                for _field_name, error_messages in form.errors.items():
                    for item in error_messages:
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
            except Exception as exception:
                return self.render(response=str(exception))

            return self.render()

    case_bug_actions = CaseBugActions(
        request=request,
        case=test_case,
        template_name=template_name
    )

    if not request.GET.get('handle') in case_bug_actions.all_actions:
        return case_bug_actions.render(response='Unrecognizable actions')

    func = getattr(case_bug_actions, request.GET['handle'])
    return func()


@require_GET
def case_plan(request, case_id):
    """Add and remove plan in plan tab"""
    test_case = get_object_or_404(TestCase, case_id=case_id)
    if request.GET.get('a'):
        # Search the plans from database
        if not request.GET.getlist('plan_id'):
            context = {
                'message': 'The case must specific one plan at leaset for '
                           'some action',
            }
            return render(
                request,
                'case/get_plan.html',
                context)

        tps = TestPlan.objects.filter(pk__in=request.GET.getlist('plan_id'))

        if not tps:
            context = {
                'testplans': tps,
                'message': 'The plan id are not exist in database at all.'
            }
            return render(
                request,
                'case/get_plan.html',
                context)

        # Add case plan action
        if request.GET['a'] == 'add':
            if not request.user.has_perm('testcases.add_testcaseplan'):
                context = {
                    'test_case': test_case,
                    'test_plans': tps,
                    'message': 'Permission denied',
                }
                return render(
                    request,
                    'case/get_plan.html',
                    context)

            for test_plan in tps:
                test_case.add_to_plan(test_plan)

        # Remove case plan action
        if request.GET['a'] == 'remove':
            if not request.user.has_perm('testcases.change_testcaseplan'):
                context = {
                    'test_case': test_case,
                    'test_plans': tps,
                    'message': 'Permission denied',
                }
                return render(
                    request,
                    'case/get_plan.html',
                    context)

            for test_plan in tps:
                test_case.remove_plan(test_plan)

    tps = test_case.plan.all()
    tps = tps.select_related('author',
                             'type',
                             'product')

    context = {
        'test_case': test_case,
        'test_plans': tps,
    }
    return render(
        request,
        'case/get_plan.html',
        context)
