# -*- coding: utf-8 -*-

from tcms.xmlrpc.serializer import XMLRPCSerializer
from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testplans.models import TestPlan
from tcms.xmlrpc.decorators import log_call


__all__ = ('get', 'update')

__xmlrpc_namespace__ = 'TestCasePlan'


@log_call(namespace=__xmlrpc_namespace__)
def get(request, case_id, plan_id):
    """
    Description: Used to load an existing test-case-plan from the database.

    Params:      $case_id - Integer: An integer representing the ID of the test case in the database.
                 $plan_id - Integer: An integer representing the ID of the test plan in the database.

    Returns:     A blessed TestCasePlan object hash

    Example:
    >>> TestCasePlan.get(81307, 3551)
    """
    tc = TestCase.objects.get(pk=case_id)
    tp = TestPlan.objects.get(pk=plan_id)
    tcp = TestCasePlan.objects.get(plan=tp, case=tc)
    return XMLRPCSerializer(model=tcp).serialize_model()


@log_call(namespace=__xmlrpc_namespace__)
def update(request, case_id, plan_id, sortkey):
    """
    Description: Updates the sortkey of the selected test-case-plan.

    Params:      $case_id - Integer: An integer representing the ID of the test case in the database.
                 $plan_id - Integer: An integer representing the ID of the test plan in the database.
                 $sortkey - Integer: An integer representing the ID of the sortkey in the database.

    Returns:     A blessed TestCasePlan object hash

    Example:
    # Update sortkey of selected test-case-plan to 450
    >>> TestCasePlan.update(81307, 3551, 450)
    """
    tc = TestCase.objects.get(pk=case_id)
    tp = TestPlan.objects.get(pk=plan_id)
    tcp = TestCasePlan.objects.get(plan=tp, case=tc)

    if isinstance(sortkey, int):
        tcp.sortkey = sortkey
        tcp.save(update_fields=['sortkey'])

    return XMLRPCSerializer(model=tcp).serialize_model()
