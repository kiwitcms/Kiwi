# -*- coding: utf-8 -*-
from django import http
from django.template import loader
from django.shortcuts import render
from django.db.models import Count, Q
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import requires_csrf_token

from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun
from tcms.project.models import Project

@require_GET
@login_required
def dashboard(request):
    """List all recent TestPlans and TestRuns"""
    user_projects = Project.objects.filter(users=request.user, enabled=True).distinct()

    filter_project = request.GET.get('project')
    if filter_project is not None and filter_project.lower() == 'all':
        filter_project = None

    if request.user.has_perm('is_superuser'):
        test_plans = TestPlan.objects
    else:
        if filter_project is not None:
            projects = Project.objects.filter(users=request.user, id=int(filter_project), enabled=True).distinct()
        else:
            projects = user_projects

        user_test_plans = []
        # Get all test plans associated with user projects
        for project in projects:
            project_testplans = project.testplans.all().values()
            for project_testplan in project_testplans:
                user_test_plans.append(project_testplan['plan_id'])

        # Make sure that list contains unique pk list
        user_test_plans_ids = set(user_test_plans)

        test_plans = TestPlan.objects.filter(plan_id__in=user_test_plans_ids)

    test_plans = test_plans.order_by('-plan_id')
    test_plans = test_plans.select_related('product', 'type')
    test_plans = test_plans.annotate(num_runs=Count('run', distinct=True))
    tps_active = test_plans.filter(is_active=True)
    test_plans_disable_count = test_plans.count() - tps_active.count()

    test_runs = TestRun.objects.filter(
        Q(manager=request.user) |
        Q(default_tester=request.user) |
        Q(case_run__assignee=request.user),
        stop_date__isnull=True,
    ).order_by('-run_id').distinct()

    context_data = {
        'test_plans_count': test_plans.count(),
        'test_plans_disable_count': test_plans_disable_count,
        'last_15_test_plans': test_plans.filter(is_active=True)[:15],

        'last_15_test_runs': test_runs[:15],

        'test_runs_count': test_runs.count(),

        'user_projects': user_projects,
    }
    return render(request, 'dashboard.html', context_data)


def navigation(request):
    """
    iframe navigation workaround until we migrate everything to patternfly
    """
    return render(request, 'navigation.html')


@requires_csrf_token
def server_error(request):
    """
        Render the error page with request object which supports
        static URLs so we can load a nice picture.
    """
    template = loader.get_template('500.html')
    return http.HttpResponseServerError(template.render({}, request))
