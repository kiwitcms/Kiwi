# -*- coding: utf-8 -*-


def order_plan_queryset(plans, field, asc=False):
    """
    Annotate the TestPlan queryset
    by calling order_by on it.
    """
    orderable_fields = (
        'id', 'name', 'author__username',
        'create_date', 'product__name', 'type'
    )
    if field in orderable_fields:
        order_by = field
        if not asc:
            order_by = '-%s' % order_by
        plans = plans.order_by(order_by)
    return plans


def order_case_queryset(cases, field, asc=False):
    """
    Annotate the TestCase queryset
    by calling order_by on it.
    """
    orderable_fields = (
        'id', 'summary', 'author__username',
        'default_tester__username', 'priority',
        'is_automated', 'category__name', 'case_status',
        'create_date'
    )
    if field in orderable_fields:
        order_by = field
        if not asc:
            order_by = '-%s' % order_by
        cases = cases.order_by(order_by)
    return cases
