# -*- coding: utf-8 -*-

import itertools

from django.conf import settings
from django.contrib import messages
from django.test import modify_settings
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView

from tcms.core.contrib.comments.utils import get_comments
from tcms.search import remove_from_request_path
from tcms.search.order import order_case_queryset
from tcms.testcases.models import TestCase, TestCaseStatus, \
    TestCasePlan
from tcms.management.models import Priority, Tag
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestExecution
from tcms.testruns.models import TestExecutionStatus
from tcms.testcases.forms import NewCaseForm, \
    SearchCaseForm, CaseNotifyForm, CloneCaseForm
from tcms.testplans.forms import SearchPlanForm
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


@method_decorator(permission_required('testcases.add_testcase'), name='dispatch')
class NewCaseView(TemplateView):

    template_name = 'testcases/mutable.html'

    def get(self, request, *args, **kwargs):
        test_plan = plan_from_request_or_none(request)

        default_form_parameters = {}
        if test_plan:
            default_form_parameters['product'] = test_plan.product_id

        form = NewCaseForm(initial=default_form_parameters)

        context_data = {
            'test_plan': test_plan,
            'form': form,
            'notify_form': CaseNotifyForm(),
        }

        return render(request, self.template_name, context_data)

    def post(self, request, *args, **kwargs):
        test_plan = plan_from_request_or_none(request)

        form = NewCaseForm(request.POST)
        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        else:
            form.populate()

        notify_form = CaseNotifyForm(request.POST)

        if form.is_valid() and notify_form.is_valid():
            test_case = self.create_test_case(form, notify_form, test_plan)
            if test_plan:
                return HttpResponseRedirect(
                    '%s?from_plan=%s' % (reverse('testcases-get', args=[test_case.pk]),
                                         test_plan.pk))

            return HttpResponseRedirect(reverse('testcases-get', args=[test_case.pk]))

        context_data = {
            'test_plan': test_plan,
            'form': form,
            'notify_form': notify_form
        }

        return render(request, self.template_name, context_data)

    def create_test_case(self, form, notify_form, test_plan):
        """Create new test case"""
        test_case = TestCase.create(author=self.request.user, values=form.cleaned_data)

        # Assign the case to the plan
        if test_plan:
            test_plan.add_case(test_case)

        update_case_email_settings(test_case, notify_form)

        return test_case


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

    :param plan: the TestPlan containing searched TestCases. None means testcases
                 are not limited to a specific TestPlan.
    :param testcases: a queryset of TestCases.
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

    :param request: the REQUEST object.
    :param plan: instance of TestPlan to restrict only those TestCases belongs to
                 the TestPlan. Can be None. As you know, query from all TestCases.
    """
    search_form = build_cases_search_form(request, True, plan)

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
            'components': case.component.only('name'),
            'tags': case.tag.only('name'),
            'case_comments': get_comments(case),
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
        case_run = TestExecution.objects.get(pk=self.caserun_id)

        # Data of TestCase
        test_case_text = case.get_text_with_version(self.case_text_version)

        # Data of TestCaseRun
        caserun_comments = get_comments(case_run)

        caserun_status = TestExecutionStatus.objects.values('pk', 'name')
        caserun_status = caserun_status.order_by('pk')
        bugs = group_case_bugs(case_run.case.get_bugs().order_by('bug_id'))

        data.update({
            'test_case': case,
            'test_case_text': test_case_text,

            'test_case_run': case_run,
            'comments_count': len(caserun_comments),
            'caserun_comments': caserun_comments,
            'caserun_logs': case_run.history.all(),
            'test_status': caserun_status,
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

    # Get the test case runs
    tcrs = test_case.case_run.select_related(
        'run', 'tested_by',
        'assignee', 'case',
        'case', 'status').order_by('run__plan', 'run')

    # Render the page
    context_data = {
        'test_case': test_case,
        'test_case_runs': tcrs,
    }

    url_params = "?case=%d" % test_case.pk
    case_edit_url = reverse('testcases-edit', args=[test_case.pk])
    test_plan = request.GET.get('from_plan', 0)
    if test_plan:
        url_params += "&from_plan=%s" % test_plan
        case_edit_url += "?from_plan=%s" % test_plan

    with modify_settings(
            MENU_ITEMS={'append': [
                ('...', [
                    (
                        _('Edit'),
                        case_edit_url
                    ),
                    (
                        _('Clone'),
                        reverse('testcases-clone') + url_params
                    ),
                    (
                        _('History'),
                        "/admin/testcases/testcase/%d/history/" % test_case.pk
                    ),
                    ('-', '-'),
                    (
                        _('Delete'),
                        reverse('admin:testcases_testcase_delete', args=[test_case.pk])
                    )])]}):
        return render(request, 'testcases/get.html', context_data)


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
    case_filter = {'pk__in': case_ids}

    test_plan = None
    # plan_pk is passed from the TestPlan.printable function
    # but it doesn't pass IDs of individual cases to be printed
    if not case_ids:
        plan_pk = request.POST.get('plan', 0)
        try:
            test_plan = TestPlan.objects.get(pk=plan_pk)
            # search cases from a TestPlan, used when printing entire plan
            case_filter = {
                'pk__in': test_plan.case.all(),
                'case_status': TestCaseStatus.objects.get(name='CONFIRMED').pk,
            }
        except (ValueError, TestPlan.DoesNotExist):
            test_plan = None

    tcs = TestCase.objects.filter(**case_filter).values(
        'case_id', 'summary', 'text'
    ).order_by('case_id')

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
              'text',
              'is_automated',
              'script',
              'arguments',
              'extra_link',
              'requirement']

    for field in fields:
        if getattr(test_case, field) != tc_form.cleaned_data[field]:
            setattr(test_case, field, tc_form.cleaned_data[field])
    try:
        if test_case.default_tester != tc_form.cleaned_data['default_tester']:
            test_case.default_tester = tc_form.cleaned_data['default_tester']
    except ObjectDoesNotExist:
        pass

    test_case.save()


@permission_required('testcases.change_testcase')
def edit(request, case_id):
    """Edit case detail"""
    try:
        test_case = TestCase.objects.select_related().get(case_id=case_id)
    except ObjectDoesNotExist:
        raise Http404

    test_plan = plan_from_request_or_none(request)
    from_plan = ""
    if test_plan:
        from_plan = "?from_plan=%d" % test_plan.pk

    if request.method == "POST":
        form = NewCaseForm(request.POST)
        if request.POST.get('product'):
            form.populate(product_id=request.POST['product'])
        elif test_plan:
            form.populate(product_id=test_plan.product_id)
        else:
            form.populate()

        n_form = CaseNotifyForm(request.POST)

        if form.is_valid() and n_form.is_valid():
            update_testcase(request, test_case, form)
            update_case_email_settings(test_case, n_form)

            return HttpResponseRedirect(
                reverse('testcases-get', args=[case_id, ]) + from_plan
            )

    else:
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

        form = NewCaseForm(initial={
            'summary': test_case.summary,
            'default_tester': default_tester,
            'requirement': test_case.requirement,
            'is_automated': test_case.is_automated,
            'script': test_case.script,
            'arguments': test_case.arguments,
            'extra_link': test_case.extra_link,
            'case_status': test_case.case_status_id,
            'priority': test_case.priority_id,
            'product': test_case.category.product_id,
            'category': test_case.category_id,
            'notes': test_case.notes,
            'text': test_case.text,
        })

        form.populate(product_id=test_case.category.product_id)

    context_data = {
        'test_case': test_case,
        'test_plan': test_plan,
        'form': form,
        'notify_form': n_form,
    }
    return render(request, 'testcases/mutable.html', context_data)


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
                        script=tc_src.script,
                        arguments=tc_src.arguments,
                        extra_link=tc_src.extra_link,
                        summary=tc_src.summary,
                        requirement=tc_src.requirement,
                        case_status=TestCaseStatus.get_proposed(),
                        category=tc_src.category,
                        priority=tc_src.priority,
                        notes=tc_src.notes,
                        text=tc_src.text,
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
