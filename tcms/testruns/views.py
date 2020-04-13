# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import UpdateView
from django_comments.models import Comment

from guardian.decorators import permission_required as object_permission_required

from tcms.core.contrib.linkreference.models import LinkReference
from tcms.core.utils import clean_request
from tcms.management.models import Build, Priority, Tag
from tcms.testcases.models import BugSystem, TestCasePlan, TestCaseStatus
from tcms.testcases.views import get_selected_testcases
from tcms.testplans.models import TestPlan
from tcms.testruns.forms import BaseRunForm, NewRunForm, SearchRunForm
from tcms.testruns.models import TestExecution, TestExecutionStatus, TestRun

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


def _open_run_get_executions(request, run):  # pylint: disable=missing-permission-required
    """Prepare for executions list in a TestRun page

    This is an internal method. Do not call this directly.
    """

    executions = run.case_run.select_related(
        'run', 'case'
    ).only('run_id',
           'status',
           'assignee',
           'tested_by',
           'case_text_version',
           'sortkey',
           'case__summary',
           'case__is_automated',
           'case__priority',
           'case__category__name'
           )

    # Continue to search the executionss with conditions
    # 4. executions preparing for render executions table
    executions = executions.filter(**clean_request(request))
    order_by = request.GET.get('order_by')
    if order_by:
        return executions.order_by(order_by)

    return executions.order_by('sortkey', 'pk')


def open_run_get_comments_subtotal(execution_ids):
    content_type = ContentType.objects.get_for_model(TestExecution)
    query_set = Comment.objects.filter(
        content_type=content_type,
        site_id=settings.SITE_ID,
        object_pk__in=execution_ids,
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


@method_decorator(
    object_permission_required('testruns.view_testrun', (TestRun, 'pk', 'pk'),
                               accept_global_perms=True),
    name='dispatch')
class GetTestRunView(TemplateView):
    """Display testrun's details"""

    template_name = 'testruns/get.html'

    def get_context_data(self, **kwargs):
        # Get the test run
        try:
            # todo: this is redundant b/c we've got self.object pointing to the
            # same object and we don't have to read it twice from the DB
            # todo: self.object however isn't present b/c this is not a DetailsView
            # and we're not calling super() anywhere
            test_run = TestRun.objects.select_related().get(pk=kwargs['pk'])
        except ObjectDoesNotExist:
            raise Http404 from None

        # Get the test executions that belong to the run
        # 2. get test run's all executions
        test_executions = _open_run_get_executions(self.request, test_run)

        status = TestExecutionStatus.objects.order_by('-weight', 'name')

        # Count the status
        # 3. calculate number of executions of each status
        status_stats_result = test_run.stats_executions_status(status)

        # Get the test execution bugs summary
        # 6. get the number of bugs of this run
        execution_bugs_count = test_run.get_bug_count()

        return {
            'object': test_run,
            'executions': _walk_executions(test_executions),
            'executions_count': len(test_executions),
            'status_stats': status_stats_result,
            'execution_bugs_count': execution_bugs_count,
            'test_status': status,
            'priorities': Priority.objects.filter(is_active=True),
            'case_own_tags': _get_tags(test_executions),
            'bug_trackers': BugSystem.objects.all(),
        }


def _get_tags(test_executions):
    """Get tag list of testcases"""

    # Get the list of testcases belong to the run
    test_cases = []
    for test_execution in test_executions:
        test_cases.append(test_execution.case_id)

    tags = Tag.objects.filter(case__in=test_cases).values_list('name', flat=True)
    tags = list(set(tags))
    tags.sort()

    return tags


def _walk_executions(test_executions):
    """Walking executions for helping rendering executions table"""

    priorities = dict(Priority.objects.values_list('pk', 'value'))
    testers, assignees = open_run_get_users(test_executions)
    execution_pks = []
    for execution in test_executions:
        execution_pks.append(execution.pk)
    comments_subtotal = open_run_get_comments_subtotal(execution_pks)

    for execution in test_executions:
        yield (execution,
               testers.get(execution.tested_by_id, None),
               assignees.get(execution.assignee_id, None),
               priorities.get(execution.case.priority_id),
               comments_subtotal.get(execution.pk, 0),
               LinkReference.objects.filter(is_defect=True,
                                            execution=execution.pk).count())


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
    caseruns = TestExecution.objects.filter(run__in=runs)
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
        caseruns = caseruns.filter(status__name__iexact=status)
    return caseruns
