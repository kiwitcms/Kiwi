# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.test import modify_settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.base import TemplateView, View

from guardian.decorators import permission_required as object_permission_required

from tcms.core.helpers.comments import get_comments
from tcms.core.response import ModifySettingsTemplateResponse
from tcms.testcases.forms import CloneCaseForm, SearchCaseForm, TestCaseForm
from tcms.testcases.forms import CaseNotifyFormSet
from tcms.testcases.models import TestCase, TestCaseStatus
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestExecution, TestExecutionStatus

TESTCASE_OPERATION_ACTIONS = (
    'search', 'sort', 'update',
    'remove',  # including remove tag from cases
    'add',  # including add tag to cases
    'change',
    'delete_cases',  # unlink cases from a TestPlan
)


# _____________________________________________________________________________
# helper functions


def plan_from_request_or_none(request):  # pylint: disable=missing-permission-required
    """Get TestPlan from REQUEST

    This method relies on the existence of from_plan within REQUEST.
    """
    test_plan_id = request.POST.get("from_plan") or request.GET.get("from_plan")
    if not test_plan_id:
        return None
    return get_object_or_404(TestPlan, pk=test_plan_id)


@method_decorator(permission_required('testcases.add_testcase'), name='dispatch')
class NewCaseView(CreateView):
    model = TestCase
    form_class = TestCaseForm
    template_name = 'testcases/mutable.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # clear fields which are set dynamically via JavaScript
        form.populate(self.request.POST.get('product', -1))
        return form

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'].update({  # pylint: disable=objects-update-used
            'author': self.request.user,
        })

        test_plan = plan_from_request_or_none(self.request)
        if test_plan:
            kwargs['initial']['product'] = test_plan.product_id

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test_plan'] = plan_from_request_or_none(self.request)
        context['notify_formset'] = kwargs.get('notify_formset') or CaseNotifyFormSet()
        return context

    def form_valid(self, form):
        test_plan = plan_from_request_or_none(self.request)

        notify_formset = CaseNotifyFormSet(self.request.POST)
        if notify_formset.is_valid():
            test_case = form.save()
            if test_plan:
                test_plan.add_case(test_case)

            notify_formset.instance = test_case
            notify_formset.save()

            return HttpResponseRedirect(reverse('testcases-get', args=[test_case.pk]))

        # taken from FormMixin.form_invalid()
        return self.render_to_response(self.get_context_data(notify_formset=notify_formset))


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
def build_cases_search_form(request,  # pylint: disable=missing-permission-required
                            populate=None, plan=None):
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


def query_testcases_from_request(request, plan=None):  # pylint: disable=missing-permission-required
    """Query TestCases according to criterias coming within REQUEST

    :param request: the REQUEST object.
    :type request: :class:`django.http.HttpRequest`

    :param plan: instance of TestPlan to restrict only those TestCases belongs to
                 the TestPlan. Can be None. As you know, query from all TestCases.
    :type plan: :class:`tcms.testplans.models.TestPlan`

    :return: Queryset with testcases and search form
    :rtype: :class:`django.db.models.query.QuerySet`, dict
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


def get_selected_testcases(request):  # pylint: disable=missing-permission-required
    """Get selected TestCases from client side

    TestCases are selected in two cases. One is user selects part of displayed
    TestCases, where there should be at least one variable named case, whose
    value is the TestCase Id. Another one is user selects all TestCases based
    on previous filter criterias even through there are non-displayed ones. In
    this case, another variable selectAll appears in the REQUEST. Whatever its
    value is.

    If neither variables mentioned exists, empty query result is returned.

    :param request: django's HttpRequest
    :type request: :class:`django.http.HttpRequest`

    :return: Queryset with testcases
    :rtype: :class:`django.db.models.query.QuerySet`
    """
    method = request.POST or request.GET
    if method.get('selectAll', None):
        plan = plan_from_request_or_none(request)
        cases, _search_form = query_testcases_from_request(request, plan)
        return cases

    return TestCase.objects.filter(pk__in=method.getlist('case'))


@method_decorator(permission_required('testcases.view_testcase'), name='dispatch')
class TestCaseSearchView(TemplateView):
    """
        Shows the search form which uses JSON RPC to fetch the results
    """

    template_name = 'testcases/search.html'

    def get_context_data(self, **kwargs):
        form = SearchCaseForm(self.request.GET)
        if self.request.GET.get('product'):
            form.populate(product_id=self.request.GET['product'])
        else:
            form.populate()

        return {
            'form': form,
        }


@method_decorator(permission_required('testruns.view_testexecution'), name='dispatch')
class TestCaseExecutionDetailPanelView(TemplateView):
    """Display execution detail in run page"""

    template_name = 'case/get_details_case_run.html'
    execution_id = None
    case_text_version = None

    def get(self, request, *args, **kwargs):
        try:
            self.execution_id = int(request.GET.get('execution_id'))
            self.case_text_version = int(request.GET.get('case_text_version'))
        except (TypeError, ValueError):
            raise Http404 from None

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        case = TestCase.objects.get(pk=kwargs['case_id'])
        execution = TestExecution.objects.get(pk=self.execution_id)

        # Data of TestCase
        test_case_text = case.get_text_with_version(self.case_text_version)

        # Data of TestExecution
        execution_comments = get_comments(execution)

        execution_status = TestExecutionStatus.objects.order_by('-weight', 'name')

        data.update({
            'test_case': case,
            'test_case_text': test_case_text,

            'execution': execution,
            'comments_count': len(execution_comments),
            'execution_comments': execution_comments,
            'execution_logs': execution.history.all(),
            'execution_status': execution_status,
        })

        return data


@method_decorator(
    object_permission_required('testcases.view_testcase', (TestCase, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class TestCaseGetView(DetailView):

    model = TestCase
    template_name = 'testcases/get.html'
    http_method_names = ['get']
    response_class = ModifySettingsTemplateResponse

    def render_to_response(self, context, **response_kwargs):
        self.response_class.modify_settings = modify_settings(
            MENU_ITEMS={'append': [
                ('...', [
                    (
                        _('Edit'),
                        reverse('testcases-edit', args=[self.object.pk])
                    ),
                    (
                        _('Clone'),
                        reverse('testcases-clone') + "?case=%d" % self.object.pk
                    ),
                    (
                        _('History'),
                        "/admin/testcases/testcase/%d/history/" % self.object.pk
                    ),
                    ('-', '-'),
                    (
                        _('Object permissions'),
                        reverse('admin:testcases_testcase_permissions', args=[self.object.pk])
                    ),
                    ('-', '-'),
                    (
                        _('Delete'),
                        reverse('admin:testcases_testcase_delete', args=[self.object.pk])
                    )])]}
        )
        return super().render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        test_case_runs = self.object.case_run.select_related(
            'run', 'tested_by',
            'assignee', 'case',
            'status').order_by('run__plan', 'run')

        context['executions'] = test_case_runs
        return context


@method_decorator(
    object_permission_required('testcases.change_testcase', (TestCase, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class EditTestCaseView(UpdateView):

    model = TestCase
    template_name = 'testcases/mutable.html'
    form_class = TestCaseForm

    def form_valid(self, form):
        notify_formset = CaseNotifyFormSet(self.request.POST, instance=self.object)
        if notify_formset.is_valid():
            notify_formset.save()
            return super().form_valid(form)

        # taken from FormMixin.form_invalid()
        return self.render_to_response(self.get_context_data(notify_formset=notify_formset))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notify_formset'] = kwargs.get('notify_formset') or \
            CaseNotifyFormSet(instance=self.object)
        return context

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.POST.get('product'):
            form.populate(product_id=self.request.POST['product'])
        else:
            form.populate(product_id=self.object.category.product_id)
        return form

    def get_initial(self):
        default_tester = None
        if self.object.default_tester_id:
            default_tester = self.object.default_tester.email

        return {
            'product': self.object.category.product_id,
            'default_tester': default_tester
        }


@method_decorator(permission_required('testcases.add_testcase'), name='dispatch')
class CloneTestCaseView(View):
    """Clone one case or multiple case into other plan or plans"""

    template_name = 'testcases/clone.html'
    http_method_names = ['get', 'post']

    def post(self, request):
        if not self._is_request_data_valid(request):
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        # Do the clone action
        clone_form = CloneCaseForm(request.POST)
        clone_form.populate(case_ids=request.POST.getlist('case'))

        if clone_form.is_valid():
            for tc_src in clone_form.cleaned_data['case']:
                tc_dest = tc_src.clone(request.user, clone_form.cleaned_data['plan'])

            # Detect the number of items and redirect to correct one
            if len(clone_form.cleaned_data['case']) == 1:
                return HttpResponseRedirect(
                    reverse('testcases-get', args=[tc_dest.pk, ])
                )

            if len(clone_form.cleaned_data['plan']) == 1:
                test_plan = clone_form.cleaned_data['plan'][0]
                return HttpResponseRedirect(
                    reverse('test_plan_url_short', args=[test_plan.pk])
                )

            # Otherwise tell the user the clone action is successful
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _('TestCase cloning was successful'))
            return HttpResponseRedirect(reverse('plans-search'))

    def get(self, request):
        if not self._is_request_data_valid(request):
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        selected_cases = get_selected_testcases(request)
        # Initial the clone case form
        clone_form = CloneCaseForm(initial={
            'case': selected_cases,
        })
        clone_form.populate(case_ids=selected_cases)

        context = {
            'form': clone_form,
        }
        return render(request, self.template_name, context)

    @staticmethod
    def _is_request_data_valid(request):
        request_data = getattr(request, request.method)

        if 'case' not in request_data:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('At least one TestCase is required'))
            return False

        return True
