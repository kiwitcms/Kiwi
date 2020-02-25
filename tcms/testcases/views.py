# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
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
        form = super().get_form()
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


def query_testcases_from_request(request, plan=None):  # pylint: disable=missing-permission-required
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


def get_selected_testcases(request):  # pylint: disable=missing-permission-required
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


class TestCaseSearchView(TemplateView):  # pylint: disable=missing-permission-required
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


class TestCaseExecutionDetailPanelView(TemplateView):  # pylint: disable=missing-permission-required
    """Display execution detail in run page"""

    template_name = 'case/get_details_case_run.html'
    execution_id = None
    case_text_version = None

    def get(self, request, *args, **kwargs):
        try:
            self.execution_id = int(request.GET.get('execution_id'))
            self.case_text_version = int(request.GET.get('case_text_version'))
        except (TypeError, ValueError):
            raise Http404

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


class TestCaseGetView(DetailView):  # pylint: disable=missing-permission-required

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


@require_POST
def printable(request,  # pylint: disable=missing-permission-required
              template_name='case/printable.html'):
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
        'pk', 'summary', 'text'
    ).order_by('pk')

    context_data = {
        'test_plan': test_plan,
        'test_cases': tcs,
    }
    return render(request, template_name, context_data)


@method_decorator(permission_required('testcases.change_testcase'), name='dispatch')
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
        form = super().get_form()
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
            test_plan = None
            tcs_src = clone_form.cleaned_data['case']
            for tc_src in tcs_src:
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
                    author=request.user,
                    default_tester=tc_src.default_tester,
                )

                # apply tags as well
                for tag in tc_src.tag.all():
                    tc_dest.add_tag(tag=tag)

                for test_plan in clone_form.cleaned_data['plan']:
                    # add new TC to selected TP
                    sortkey = test_plan.get_case_sortkey()
                    test_plan.add_case(tc_dest, sortkey)

                    # clone TC category b/c we may be cloning a 'linked'
                    # TC which has a different Product that doesn't have the
                    # same categories yet
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

                    # clone TC components b/c we may be cloning a 'linked'
                    # TC which has a different Product that doesn't have the
                    # same components yet
                    for component in tc_src.component.all():
                        try:
                            new_c = test_plan.product.component.get(name=component.name)
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
