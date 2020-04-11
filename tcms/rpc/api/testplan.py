# -*- coding: utf-8 -*-

from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.management.models import Tag
from tcms.rpc import utils
from tcms.rpc.api.forms.testplan import EditPlanForm, NewPlanForm
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import TestCase, TestCasePlan
from tcms.testplans.models import TestPlan

__all__ = (
    'create',
    'update',
    'filter',

    'add_case',
    'remove_case',

    'add_tag',
    'remove_tag',

    'add_attachment',
    'list_attachments',
)


@permissions_required('testplans.add_testplan')
@rpc_method(name='TestPlan.create')
def create(values, **kwargs):
    """
    .. function:: XML-RPC TestPlan.create(values)

        Create new Test Plan object and store it in the database.

        :param values: Field values for :class:`tcms.testplans.models.TestPlan`
        :type values: dict
        :return: Serialized :class:`tcms.testplans.models.TestPlan` object
        :rtype: dict
        :raises: PermissionDenied if missing *testplans.add_testplan* permission
        :raises: ValueError if data validation fails

        Minimal parameters::

            >>> values = {
                'product': 61,
                'product_version': 93,
                'name': 'Testplan foobar',
                'type': 1,
                'parent': 150,
                'text':'Testing TCMS',
            }
            >>> TestPlan.create(values)
    """
    request = kwargs.get(REQUEST_KEY)

    if not (values.get('author') or values.get('author_id')):
        values['author'] = request.user.pk

    form = NewPlanForm(values)
    form.populate(product_id=values['product'])

    if form.is_valid():
        test_plan = form.save()
    else:
        raise ValueError(form_errors_to_list(form))

    return test_plan.serialize()


@rpc_method(name='TestPlan.filter')
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC TestPlan.filter(query)

        Perform a search and return the resulting list of test plans.

        :param query: Field lookups for :class:`tcms.testplans.models.TestPlan`
        :type query: dict
        :return: List of serialized :class:`tcms.testplans.models.TestPlan` objects
        :rtype: list(dict)
    """

    if query is None:
        query = {}

    return TestPlan.to_xmlrpc(query)


@permissions_required('testplans.add_testplantag')
@rpc_method(name='TestPlan.add_tag')
def add_tag(plan_id, tag_name, **kwargs):
    """
    .. function:: XML-RPC TestPlan.add_tag(plan_id, tag_name)

        Add a tag to the specified test plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param tag_name: Tag name to add
        :type tag_name: str
        :return: None
        :raises: PermissionDenied if missing *testplans.add_testplantag* permission
        :raises: TestPlan.DoesNotExist if object specified by PK doesn't exist
        :raises: Tag.DoesNotExist if missing *management.add_tag* permission and *tag_name*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag, _ = Tag.get_or_create(request.user, tag_name)
    TestPlan.objects.get(pk=plan_id).add_tag(tag)


@permissions_required('testplans.delete_testplantag')
@rpc_method(name='TestPlan.remove_tag')
def remove_tag(plan_id, tag_name):
    """
    .. function:: XML-RPC TestPlan.remove_tag(plan_id, tag_name)

        Remove tag from the specified test plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param tag_name: Tag name to remove
        :type tag_name: str
        :return: None
        :raises: PermissionDenied if missing *testplans.delete_testplantag* permission
        :raises: DoesNotExist if objects specified don't exist
    """
    tag = Tag.objects.get(name=tag_name)
    TestPlan.objects.get(pk=plan_id).remove_tag(tag)


@permissions_required('testplans.change_testplan')
@rpc_method(name='TestPlan.update')
def update(plan_id, values):
    """
    .. function:: XML-RPC TestPlan.update(plan_id, values)

        Update the fields of the selected test plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param values: Field values for :class:`tcms.testplans.models.TestPlan`
        :type values: dict
        :return: Serialized :class:`tcms.testplans.models.TestPlan` object
        :rtype: dict
        :raises: TestPlan.DoesNotExist if object specified by PK doesn't exist
        :raises: PermissionDenied if missing *testplans.change_testplan* permission
        :raises: ValueError if validations fail
    """
    test_plan = TestPlan.objects.get(pk=plan_id)
    form = EditPlanForm(values, instance=test_plan)
    if form.is_valid():
        test_plan = form.save()
    else:
        raise ValueError(form_errors_to_list(form))

    return test_plan.serialize()


@permissions_required('testcases.add_testcaseplan')
@rpc_method(name='TestPlan.add_case')
def add_case(plan_id, case_id):
    """
    .. function:: XML-RPC TestPlan.add_case(plan_id, case_id)

        Link test case to the given plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param case_id: PK of TestCase to be added to plan
        :type case_id: int
        :return: None
        :raises: TestPlan.DoesNotExit or TestCase.DoesNotExist if objects specified
                 by PKs are missing
        :raises: PermissionDenied if missing *testcases.add_testcaseplan* permission
    """
    plan = TestPlan.objects.get(pk=plan_id)
    case = TestCase.objects.get(pk=case_id)
    plan.add_case(case)


@permissions_required('testcases.delete_testcaseplan')
@rpc_method(name='TestPlan.remove_case')
def remove_case(plan_id, case_id):
    """
    .. function:: XML-RPC TestPlan.remove_case(plan_id, case_id)

        Unlink a test case from the given plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param case_id: PK of TestCase to be removed from plan
        :type case_id: int
        :return: None
        :raises: PermissionDenied if missing *testcases.delete_testcaseplan* permission
    """
    TestCasePlan.objects.filter(case=case_id, plan=plan_id).delete()


@permissions_required('attachments.view_attachment')
@rpc_method(name='TestPlan.list_attachments')
def list_attachments(plan_id, **kwargs):
    """
    .. function:: XML-RPC TestPlan.list_attachments(plan_id)

        List attachments for the given TestPlan.

        :param plan_id: PK of TestPlan to inspect
        :type plan_id: int
        :return: A list containing information and download URLs for attachements
        :rtype: list
        :raises: TestPlan.DoesNotExit if object specified by PK is missing
    """
    plan = TestPlan.objects.get(pk=plan_id)
    request = kwargs.get(REQUEST_KEY)
    return utils.get_attachments_for(request, plan)


@permissions_required('attachments.add_attachment')
@rpc_method(name='TestPlan.add_attachment')
def add_attachment(plan_id, filename, b64content, **kwargs):
    """
    .. function:: XML-RPC TestPlan.add_attachment(plan_id, filename, b64content)

        Add attachment to the given TestPlan.

        :param plan_id: PK of TestPlan
        :type plan_id: int
        :param filename: File name of attachment, e.g. 'logs.txt'
        :type filename: str
        :param b64content: Base64 encoded content
        :type b64content: str
        :return: None
    """
    utils.add_attachment(
        plan_id,
        'testplans.TestPlan',
        kwargs.get(REQUEST_KEY).user,
        filename,
        b64content)
