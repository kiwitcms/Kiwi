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

from tcms.core.forms import SimpleCommentForm
from tcms.core.response import ModifySettingsTemplateResponse
from tcms.testcases.models import BugSystem, TestCasePlan, TestCaseStatus, TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.forms import NewRunForm, SearchRunForm
from tcms.testruns.models import TestExecutionStatus, TestRun
from tcms.core.contrib.linkreference.forms import LinkReferenceForm

User = get_user_model()  # pylint: disable=invalid-name


@method_decorator(permission_required('testruns.add_testrun'), name='dispatch')
class NewTestRunView(View):
    """Display new test run page."""

    template_name = 'testruns/mutable.html'
    http_method_names = ['post', 'get']

    def get(self, request, form_initial=None, is_cloning=False):
        plan_id = request.GET.get('p')
        if not plan_id:
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Creating a TestRun requires a TestPlan, select one'))
            return HttpResponseRedirect(reverse('plans-search'))

        if not request.GET.get('c'):
            messages.add_message(request,
                                 messages.ERROR,
                                 _('Creating a TestRun requires at least one TestCase'))
            return HttpResponseRedirect(reverse('test_plan_url_short', args=[plan_id]))

        test_cases = TestCase.objects.filter(pk__in=request.GET.getlist('c'))

        # note: ordered by pk for test_show_create_new_run_page()
        tcs_values = test_cases.select_related('author',
                                               'case_status',
                                               'category',
                                               'priority').order_by('pk')

        test_plan = TestPlan.objects.get(pk=plan_id)
        if not form_initial:
            form_initial = {
                'summary': 'Test run for %s' % test_plan.name,
                'manager': test_plan.author.email,
                'default_tester': request.user.email,
                'notes': '',
                'plan': plan_id,
            }
        form = NewRunForm(initial=form_initial)
        form.populate(plan_id)

        context_data = {
            'test_cases': tcs_values,
            'form': form,
            'disabled_cases': get_disabled_test_cases_count(test_cases),
            'is_cloning': is_cloning,
        }
        return render(request, self.template_name, context_data)

    def post(self, request):
        form = NewRunForm(data=request.POST)
        form.populate(request.POST.get('plan'))

        if form.is_valid():
            test_run = form.save()
            loop = 1

            for case in form.cleaned_data['case']:
                try:
                    tcp = TestCasePlan.objects.get(plan=form.cleaned_data['plan'], case=case)
                    sortkey = tcp.sortkey
                except ObjectDoesNotExist:
                    sortkey = loop * 10

                test_run.create_execution(case=case, sortkey=sortkey,
                                          assignee=form.cleaned_data['default_tester'])
                loop += 1

            return HttpResponseRedirect(
                reverse('testruns-get', args=[test_run.pk, ])
            )

        test_cases = TestCase.objects.filter(pk__in=request.POST.getlist('case'))

        tcs_values = test_cases.select_related('author',
                                               'case_status',
                                               'category',
                                               'priority').order_by('pk')
        context_data = {
            'test_cases': tcs_values,
            'form': form,
            'disabled_cases': get_disabled_test_cases_count(test_cases)
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
        context['confirmed_statuses'] = TestCaseStatus.objects.filter(is_confirmed=True)
        context['link_form'] = LinkReferenceForm()
        context['bug_trackers'] = BugSystem.objects.all()
        context['comment_form'] = SimpleCommentForm()
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
                        reverse('testruns-clone', args=[self.object.pk])
                    ),
                    (
                        _('History'),
                        "/admin/testruns/testrun/%d/history/" % self.object.pk
                    ),
                    ('-', '-'),
                    (
                        _('Object permissions'),
                        reverse('admin:testruns_testrun_permissions', args=[self.object.pk])
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
    form_class = NewRunForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.populate(self.object.plan_id)

        return form

    def get_initial(self):
        return {
            'manager': self.object.manager,
            'default_tester': self.object.default_tester,
        }


@method_decorator(permission_required('testruns.add_testrun'), name='dispatch')
class CloneTestRunView(NewTestRunView):
    # note: post is handled directly by NewTestRunView
    # b/c <form action> points to testruns-new URL
    http_method_names = ['get']

    def get(self, request, pk):  # pylint: disable=arguments-differ
        test_run = get_object_or_404(TestRun, pk=pk)

        request.GET._mutable = True  # pylint: disable=protected-access
        request.GET['p'] = test_run.plan_id
        request.GET.setlist('c', test_run.case_run.all().values_list('case', flat=True))

        form_initial = {
            'summary': _('Clone of ') + test_run.summary,
            'notes': test_run.notes,
            'manager': test_run.manager,
            'build': test_run.build_id,
            'default_tester': test_run.default_tester,
            'plan': test_run.plan_id,
        }

        return super().get(request, form_initial=form_initial, is_cloning=True)


@method_decorator(permission_required('testruns.change_testrun'), name='dispatch')
class ChangeTestRunStatusView(View):
    """Change test run finished or running"""

    http_method_names = ['get']

    def get(self, request, pk):
        test_run = get_object_or_404(TestRun, pk=pk)

        test_run.update_completion_status(request.GET.get('finished') == '1')
        test_run.save()

        return HttpResponseRedirect(reverse('testruns-get', args=[pk, ]))


def get_disabled_test_cases_count(test_cases):
    return test_cases.filter(case_status__is_confirmed=False).count()
