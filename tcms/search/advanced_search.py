# -*- coding: utf-8 -*-

"""
Advance search implementations
"""

import time

from django.db.models import Count
from django.shortcuts import render
from django.views.decorators.http import require_GET

from tcms.management.models import Priority, Product
from tcms.search.forms import CaseForm, RunForm, PlanForm
from tcms.search.order import order_targets
from tcms.search.query import SmartDjangoQuery
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan, PlanType
from tcms.testruns.models import TestRun
from tcms.search import fmt_queries, remove_from_request_path, replace_keys


@require_GET
def advance_search(request):
    data = request.GET
    target = data.get('target')
    plan_form = PlanForm(data)
    case_form = CaseForm(data)
    run_form = RunForm(data)
    # Update MultipleModelChoiceField on each form dynamically
    plan_form.populate(data)
    case_form.populate(data)
    run_form.populate(data)
    all_forms = (plan_form, case_form, run_form)

    rendered_errors = _render_errors(request, data, all_forms)
    if rendered_errors:
        return rendered_errors

    start = time.time()
    results = _query(plan_form.cleaned_data,
                     run_form.cleaned_data,
                     case_form.cleaned_data,
                     target)
    results = order_targets(target, results, data)
    end = time.time()
    timecost = round(end - start, 3)
    queries = []
    for form in all_forms:
        queries.append(form.cleaned_data)
    queries = fmt_queries(*queries)
    queries['Target'] = target
    return _render_results(request, results, timecost, queries)


def _render_errors(request, data, forms):  # pylint: disable=inconsistent-return-statements
    errors = []
    for form in forms:
        if form.is_valid():
            errors.append(form.errors)

    if errors or not data:
        product_choice = []
        for product in Product.objects.all():
            product_choice.append((product.pk, product.name))
        plan_type_choices = PlanType.objects.all()  # pylint: disable=unused-variable
        errors = _fmt_errors(errors)
        priorities = Priority.objects.filter(  # pylint: disable=unused-variable
            is_active=True).order_by('value')

        return render(request, 'search/advanced_search.html', locals())


def _query(plan_query, run_query, case_query, target):
    plans = SmartDjangoQuery(plan_query, TestPlan.__name__)
    runs = SmartDjangoQuery(run_query, TestRun.__name__)
    cases = SmartDjangoQuery(case_query, TestCase.__name__)

    return _sum_orm_queries(plans, cases, runs, target)


def _sum_orm_queries(plans, cases, runs, target):
    plans = plans.evaluate()
    cases = cases.evaluate()
    runs = runs.evaluate()
    if target == 'run':
        return _get_run_target(plans, cases, runs)
    if target == 'plan':
        return _get_plan_target(plans, cases, runs)
    if target == 'case':
        return _get_case_target(plans, cases, runs)
    raise ValueError('Invalid target')


def _get_run_target(plans, cases, runs):
    if not plans and not cases and runs is None:
        runs = TestRun.objects.none()
    if runs is None:
        runs = TestRun.objects.all()
    if cases:
        runs = runs.filter(case_run__case__in=cases).distinct()
    if plans:
        runs = runs.filter(plan__in=plans).distinct()
    return runs


def _get_plan_target(plans, cases, runs):
    if not cases and not runs and plans is None:
        plans = TestPlan.objects.none()
    if plans is None:
        plans = TestPlan.objects.all()
    if cases:
        plans = plans.filter(case__in=cases).distinct()
    if runs:
        plans = plans.filter(run__in=runs).distinct()
    plans = plans.annotate(num_cases=Count('case', distinct=True),
                           num_runs=Count('run', distinct=True))
    return plans


def _get_case_target(plans, cases, runs):
    if not plans and not runs and cases is None:
        cases = TestCase.objects.none()
    if cases is None:
        cases = TestCase.objects.all()
    if runs:
        cases = cases.filter(case_run__run__in=runs).distinct()
    if plans:
        cases = cases.filter(plan__in=plans).distinct()
    return cases


def _render_results(request, results, time_cost, queries):
    """Using a SQL "in" query and PKs as the arguments"""
    klasses = {
        'plan': {'class': TestPlan, 'result_key': 'test_plans'},
        'case': {'class': TestCase, 'result_key': 'test_cases'},
        'run': {'class': TestRun, 'result_key': 'test_runs'}
    }
    asc = bool(request.GET.get('asc', None))
    query_url = remove_from_request_path(request, 'order_by')
    if asc:
        query_url = remove_from_request_path(query_url, 'asc')
    else:
        query_url = '%s&asc=True' % query_url
    context_data = {
        klasses[request.GET['target']]['result_key']: results,
        'time_cost': time_cost,
        'queries': queries,
        'query_url': query_url,
    }
    return render(request, 'search/results.html', context_data)


def _fmt_errors(form_errors):
    """
    Format errors collected in a Django Form
    for a better appearance.
    """
    errors = []
    for error in form_errors:
        for key, value in error.items():
            key = replace_keys(key)
            if isinstance(value, list):
                value = ', '.join(map(str, value))
            errors.append((key, value))
    return errors
