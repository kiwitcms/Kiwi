# -*- coding: utf-8 -*-

"""
Advance search implementations
"""

import time

from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET

from tcms.core.helpers.cache import cached_entities
from tcms.core.utils.raw_sql import RawSQL
from tcms.management.models import Priority
from tcms.search.forms import CaseForm, RunForm, PlanForm
from tcms.search.order import order_targets
from tcms.search.query import SmartDjangoQuery
from tcms.testcases.models import TestCase
from tcms.testplans.models import TestPlan
from tcms.testruns.models import TestRun


@require_GET
def advance_search(request):
    """View of /advance-search/"""
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

    errors = []
    for form in all_forms:
        if form.is_valid():
            errors.append(form.errors)

    if errors or not data:
        product_choice = []
        for product in cached_entities('product'):
            product_choice.append((product.pk, product.name))
        plan_type_choices = cached_entities('plantype')  # pylint: disable=unused-variable
        errors = _fmt_errors(errors)
        priorities = Priority.objects.filter(  # pylint: disable=unused-variable
            is_active=True).order_by('value')

        return render(request, 'search/advanced_search.html', locals())

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
        if not plans and not cases:
            if runs is None:
                runs = TestRun.objects.none()
        if runs is None:
            runs = TestRun.objects.all()
        if cases:
            runs = runs.filter(case_run__case__in=cases).distinct()
        if plans:
            runs = runs.filter(plan__in=plans).distinct()
        return runs
    if target == 'plan':
        if not cases and not runs:
            if plans is None:
                plans = TestPlan.objects.none()
        if plans is None:
            plans = TestPlan.objects.all()
        if cases:
            plans = plans.filter(case__in=cases).distinct()
        if runs:
            plans = plans.filter(run__in=runs).distinct()
        plans = plans.extra(select={
            'num_cases': RawSQL.num_cases,
            'num_runs': RawSQL.num_runs,
            'num_children': RawSQL.num_plans,
        })
        return plans
    if target == 'case':
        if not plans and not runs:
            if cases is None:
                cases = TestCase.objects.none()
        if cases is None:
            cases = TestCase.objects.all()
        if runs:
            cases = cases.filter(case_run__run__in=runs).distinct()
        if plans:
            cases = cases.filter(plan__in=plans).distinct()
        return cases
    raise ValueError('Invalid target')


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


def remove_from_request_path(request, name):
    """
    Remove a parameter from request.get_full_path()\n
    and return the modified path afterwards.
    """
    if isinstance(request, HttpRequest):
        path = request.get_full_path()
    else:
        path = request
    path = path.split('?')
    if len(path) > 1:
        path = path[1].split('&')
    else:
        return None

    for p in path:
        if p.startswith(name):
            path.remove(p)

    path = '&'.join(path)
    return '?' + path


def _fmt_errors(form_errors):
    """
    Format errors collected in a Django Form
    for a better appearance.
    """
    errors = []
    for error in form_errors:
        for key, value in error.items():
            key = key.replace('p_product', 'product')
            key = key.replace('p_', 'product ')
            key = key.replace('cs_', 'case ')
            key = key.replace('pl_', 'plan ')
            key = key.replace('r_', 'run ')
            key = key.replace('_', ' ')
            if isinstance(value, list):
                value = ', '.join(map(str, value))
            errors.append((key, value))
    return errors


def fmt_queries(*queries):
    """
    Format the queries string.
    """
    results = {}
    for _query in queries:
        for key, value in _query.items():
            key = key.replace('p_product', 'product')
            key = key.replace('p_', 'product ')
            key = key.replace('cs_', 'case ')
            key = key.replace('pl_', 'plan ')
            key = key.replace('r_', 'run ')
            key = key.replace('_', ' ')
            if isinstance(value, bool) or value:
                if isinstance(value, QuerySet):
                    try:
                        value = ', '.join(o.name for o in value)
                    except AttributeError:
                        try:
                            value = ', '.join(o.value for o in value)
                        except AttributeError:
                            value = ', '.join(value)
                if isinstance(value, list):
                    value = ', '.join(map(str, value))
                results[key] = value
    return results
