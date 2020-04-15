# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.test import modify_settings
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import UpdateView

from guardian.decorators import permission_required as object_permission_required

from tcms.core.response import ModifySettingsTemplateResponse
from tcms.management.models import Build
from tcms.testcases.models import TestCasePlan, TestCaseStatus
from tcms.testcases.views import get_selected_testcases
from tcms.testplans.models import TestPlan
from tcms.testruns.forms import BaseRunForm, NewRunForm, SearchRunForm
from tcms.testruns.models import TestExecutionStatus, TestRun

User = get_user_model()  # pylint: disable=invalid-name


@method_decorator(permission_required('testruns.add_testrun'), name='dispatch')
class CreateTestRunView(View):
    """Display the create test run page."""

    template_name = 'testruns/mutable.html'
    http_method_names = ['post']

    def post(self, request):
        # If from_plan does not exist will redirect to plans for select a plan
        plan_id = request.POST.get('from_plan')
        if not plan_id:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Creating a TestRun requires a TestPlan, select one'))
            return HttpResponseRedirect(reverse('plans-search'))

        if not request.POST.get('case'):
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Creating a TestRun requires at least one TestCase'))
            return HttpResponseRedirect(reverse('test_plan_url_short', args=[plan_id]))

        # Ready to write cases to test plan
        test_cases = get_selected_testcases(request)
        test_plan = TestPlan.objects.get(pk=plan_id)

        # note: ordered by pk for test_show_create_new_run_page()
        tcs_values = test_cases.select_related('author',
                                               'case_status',
                                               'category',
                                               'priority').order_by('pk')

        if request.POST.get('POSTING_TO_CREATE'):
            form = NewRunForm(request.POST)
            form.populate(product_id=test_plan.product_id)

            if form.is_valid():
                # Process the data in form.cleaned_data
                default_tester = form.cleaned_data['default_tester']

                test_run = TestRun.objects.create(
                    product_version=test_plan.product_version,
                    stop_date=None,
                    summary=form.cleaned_data.get('summary'),
                    notes=form.cleaned_data.get('notes'),
                    plan=test_plan,
                    build=form.cleaned_data['build'],
                    manager=form.cleaned_data['manager'],
                    default_tester=default_tester,
                )

                loop = 1
                for case in form.cleaned_data['case']:
                    try:
                        tcp = TestCasePlan.objects.get(plan=test_plan, case=case)
                        sortkey = tcp.sortkey
                    except ObjectDoesNotExist:
                        sortkey = loop * 10

                    test_run.add_case_run(case=case, sortkey=sortkey,
                                          assignee=default_tester)
                    loop += 1

                return HttpResponseRedirect(
                    reverse('testruns-get', args=[test_run.pk, ])
                )

        else:
            form = NewRunForm(initial={
                'summary': 'Test run for %s' % test_plan.name,
                'manager': test_plan.author.email,
                'default_tester': request.user.email,
                'notes': '',
            })
            form.populate(product_id=test_plan.product_id)

        context_data = {
            'test_plan': test_plan,
            'test_cases': tcs_values,
            'form': form,
        }
        return render(request, self.template_name, context_data)


@method_decorator(permission_required('testruns.view_testrun'), name='dispatch')
class SearchTestRunView(TemplateView):

    template_name = 'testruns/search.html'

    def get_context_data(self, **kwargs):
        form = SearchRunForm(self.request.GET)
        form.populate(product_id=self.request.GET.get('product'))

        return {
            'form': form,
        }


@method_decorator(
    object_permission_required('testruns.view_testrun', (TestRun, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class GetTestRunView(DetailView):

    template_name = 'testruns/get.html'
    http_method_names = ['get']
    model = TestRun
    response_class = ModifySettingsTemplateResponse

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['execution_statuses'] = TestExecutionStatus.objects.order_by('-weight', 'name')
        return context

    def render_to_response(self, context, **response_kwargs):
        self.response_class.modify_settings = modify_settings(
            MENU_ITEMS={'append': [
                ('...', [
                    (
                        _('Edit'),
                        reverse('testruns-edit', args=[self.object.pk])
                    ),
                    (
                        _('Clone'),
                        # todo: URL accepts POST, need to refactor to use GET+POST
                        # e.g. runs/3/clone/
                        reverse('testruns-clone', args=[self.object.pk])
                    ),
                    (
                        _('History'),
                        "/admin/testruns/testrun/%d/history/" % self.object.pk
                    ),
                    ('-', '-'),
                    (
                        _('Delete'),
                        reverse('admin:testruns_testrun_delete', args=[self.object.pk])
                    )])]}
        )
        return super().render_to_response(context, **response_kwargs)


@method_decorator(
    object_permission_required('testruns.change_testrun', (TestRun, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class EditTestRunView(UpdateView):
    model = TestRun
    template_name = 'testruns/mutable.html'
    form_class = BaseRunForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test_plan'] = self.object.plan
        context['builds'] = Build.objects.filter(product=self.object.plan.product, is_active=True)

        return context

    def get_form(self, form_class=None):
        form = super().get_form()
        form.populate(self.object.plan.product_id)

        return form

    def get_initial(self):
        return {
            'manager': self.object.manager,
            'default_tester': self.object.default_tester,
        }


@method_decorator(permission_required('testruns.add_testrun'), name='dispatch')
class CloneTestRunView(View):
    """Clone cases from filter caserun"""

    template_name = 'testruns/mutable.html'
    http_method_names = ['post']

    def post(self, request, pk):
        test_run = get_object_or_404(TestRun, pk=pk)
        confirmed_case_status = TestCaseStatus.get_confirmed()
        disabled_cases = 0

        if request.POST.get('case_run'):
            test_cases = []
            for test_case_run in test_run.case_run.filter(pk__in=request.POST.getlist('case_run')):
                if test_case_run.case.case_status == confirmed_case_status:
                    test_cases.append(test_case_run.case)
                else:
                    disabled_cases += 1
        else:
            test_cases = None

        if not test_cases:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('At least one TestCase is required'))
            return HttpResponseRedirect(reverse('testruns-get', args=[pk]))

        form = NewRunForm(initial={
            'summary': _('Clone of ') + test_run.summary,
            'notes': test_run.notes,
            'manager': test_run.manager,
            'build': test_run.build_id,
            'default_tester': test_run.default_tester,
        })
        form.populate(product_id=test_run.plan.product_id)

        context_data = {
            'is_cloning': True,
            'disabled_cases': disabled_cases,
            'test_plan': test_run.plan,
            'test_cases': test_cases,
            'form': form,
        }
        return render(request, self.template_name, context_data)


@method_decorator(permission_required('testruns.change_testrun'), name='dispatch')
class ChangeTestRunStatusView(View):
    """Change test run finished or running"""

    http_method_names = ['get']

    def get(self, request, pk):
        test_run = get_object_or_404(TestRun, pk=pk)

        test_run.update_completion_status(request.GET.get('finished') == '1')
        test_run.save()

        return HttpResponseRedirect(reverse('testruns-get', args=[pk, ]))
