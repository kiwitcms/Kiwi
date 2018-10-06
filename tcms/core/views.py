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


@require_GET
@login_required
def dashboard(request):
    """List all recent TestPlans and TestRuns"""
    test_plans = TestPlan.objects.filter(
        author=request.user
    ).order_by(
        '-plan_id'
    ).select_related(
        'product', 'type'
    ).annotate(
        num_runs=Count('run', distinct=True)
    )
    test_plans_disable_count = test_plans.filter(is_active=False).count()

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
