# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.dao.shared.attachment_dao import attachment_dao
from tcms.dao.shared.tag_dao import tag_dao
from tcms.dao.testcases.test_case_dao import test_case_dao
from tcms.dao.testplans.test_plan_dao import test_plan_dao
from tcms.rpc.api.forms.testplan import EditPlanForm, NewPlanAPIForm
from tcms.rpc.decorators import permissions_required


@permissions_required("testplans.add_testplan")
@rpc_method(name="TestPlan.create")
def create(values, **kwargs):
    """
    .. function:: RPC TestPlan.create(values)

        Create new Test Plan object and store it in the database.

        :param values: Field values for :class:`tcms.testplans.models.TestPlan`
        :type values: dict
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`tcms.testplans.models.TestPlan` object
        :rtype: dict
        :raises PermissionDenied: if missing *testplans.add_testplan* permission
        :raises ValueError: if data validation fails

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

    if not values.get("author"):
        values["author"] = request.user.pk

    if not values.get("is_active"):
        values["is_active"] = True

    form = NewPlanAPIForm(values)
    form.populate(product_id=values["product"])

    if form.is_valid():
        test_plan = form.save()
        # auto_now_add will *always* set current date! see:
        # https://docs.djangoproject.com/en/6.0/ref/models/fields/#django.db.models.DateField.auto_now_add
        if "create_date" in form.cleaned_data:
            test_plan.create_date = form.cleaned_data["create_date"]
            test_plan.save()

        test_plan_dao.save(test_plan)
        result = model_to_dict(test_plan, exclude=["tag"])

        # b/c value is set in the DB directly and if None
        # model_to_dict() will not return it
        result["create_date"] = test_plan.create_date
        return result

    raise ValueError(list(form.errors.items()))


@permissions_required("testplans.view_testplan")
@rpc_method(name="TestPlan.filter")
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC TestPlan.filter(query)

        Perform a search and return the resulting list of test plans.

        :param query: Field lookups for :class:`tcms.testplans.models.TestPlan`
        :type query: dict
        :return: List of serialized :class:`tcms.testplans.models.TestPlan` objects
        :rtype: list(dict)
    """

    if query is None:
        query = {}

    return test_plan_dao.filter(query)


@permissions_required("testplans.add_testplantag")
@rpc_method(name="TestPlan.add_tag")
def add_tag(plan_id, tag_name, **kwargs):
    """
    .. function:: RPC TestPlan.add_tag(plan_id, tag_name)

        Add a tag to the specified test plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param tag_name: Tag name to add
        :type tag_name: str
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :raises PermissionDenied: if missing *testplans.add_testplantag* permission
        :raises TestPlan.DoesNotExist: if object specified by PK doesn't exist
        :raises Tag.DoesNotExist: if missing *management.add_tag* permission and *tag_name*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag_obj, _ = tag_dao.get_or_create(request.user, tag_name)
    plan = test_plan_dao.get_by_id(plan_id)
    tag_dao.add_tag(plan, tag_obj)


@permissions_required("testplans.delete_testplantag")
@rpc_method(name="TestPlan.remove_tag")
def remove_tag(plan_id, tag_name):
    """
    .. function:: RPC TestPlan.remove_tag(plan_id, tag_name)

        Remove tag from the specified test plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param tag_name: Tag name to remove
        :type tag_name: str
        :raises PermissionDenied: if missing *testplans.delete_testplantag* permission
        :raises DoesNotExist: if objects specified don't exist
    """
    tag_obj = tag_dao.get_by_name(tag_name)
    plan = test_plan_dao.get_by_id(plan_id)
    tag_dao.remove_tag(plan, tag_obj)


@permissions_required("testplans.change_testplan")
@rpc_method(name="TestPlan.update")
def update(plan_id, values):
    """
    .. function:: RPC TestPlan.update(plan_id, values)

        Update the fields of the selected test plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param values: Field values for :class:`tcms.testplans.models.TestPlan`
        :type values: dict
        :return: Serialized :class:`tcms.testplans.models.TestPlan` object
        :rtype: dict
        :raises TestPlan.DoesNotExist: if object specified by PK doesn't exist
        :raises PermissionDenied: if missing *testplans.change_testplan* permission
        :raises ValueError: if validations fail
    """
    test_plan = test_plan_dao.get_by_id(plan_id)
    form = EditPlanForm(values, instance=test_plan)
    if form.is_valid():
        test_plan = form.save()
        test_plan_dao.save(test_plan)
        result = model_to_dict(test_plan, exclude=["tag"])

        # b/c value is set in the DB directly and if None
        # model_to_dict() will not return it
        result["create_date"] = test_plan.create_date
        return result

    raise ValueError(list(form.errors.items()))


@permissions_required("testcases.add_testcaseplan")
@rpc_method(name="TestPlan.add_case")
def add_case(plan_id, case_id):
    """
    .. function:: RPC TestPlan.add_case(plan_id, case_id)

        Link test case to the given plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param case_id: PK of TestCase to be added to plan
        :type case_id: int
        :return: Serialized :class:`tcms.testcases.models.TestCase` object
                 augmented with a 'sortkey' value
        :rtype: dict
        :raises TestPlan.DoesNotExit or TestCase.DoesNotExist: if objects specified
                 by PKs are missing
        :raises PermissionDenied: if missing *testcases.add_testcaseplan* permission
    """
    plan = test_plan_dao.get_by_id(plan_id)
    case = test_case_dao.get_by_id(case_id)
    return test_plan_dao.add_case(plan, case)


@permissions_required("testcases.delete_testcaseplan")
@rpc_method(name="TestPlan.remove_case")
def remove_case(plan_id, case_id):
    """
    .. function:: RPC TestPlan.remove_case(plan_id, case_id)

        Unlink a test case from the given plan.

        :param plan_id: PK of TestPlan to modify
        :type plan_id: int
        :param case_id: PK of TestCase to be removed from plan
        :type case_id: int
        :raises PermissionDenied: if missing *testcases.delete_testcaseplan* permission
    """
    test_plan_dao.remove_case(plan_id, case_id)


@permissions_required("testcases.change_testcaseplan")
@rpc_method(name="TestPlan.update_case_order")
def update_case_order(plan_id, case_id, sortkey):
    """
    .. function:: RPC TestPlan.update_case_order(plan_id, case_id, sortkey)

        Update sortkey which controls display order of the given test case in
        the given test plan.

        :param plan_id: PK of TestPlan holding the selected TestCase
        :type plan_id: int
        :param case_id: PK of TestCase to be modified
        :type case_id: int
        :param sortkey: Ordering value, e.g. 10, 20, 30
        :type sortkey: int
        :raises PermissionDenied: if missing *testcases.delete_testcaseplan* permission
    """
    test_plan_dao.update_case_order(plan_id, case_id, sortkey)


@permissions_required("attachments.view_attachment")
@rpc_method(name="TestPlan.list_attachments")
def list_attachments(plan_id, **kwargs):
    """
    .. function:: RPC TestPlan.list_attachments(plan_id)

        List attachments for the given TestPlan.

        :param plan_id: PK of TestPlan to inspect
        :type plan_id: int
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: A list containing information and download URLs for attachements
        :rtype: list
        :raises TestPlan.DoesNotExit: if object specified by PK is missing
    """
    plan = test_plan_dao.get_by_id(plan_id)
    request = kwargs.get(REQUEST_KEY)
    return attachment_dao.list_attachments(request, plan)


@permissions_required("attachments.add_attachment")
@rpc_method(name="TestPlan.add_attachment")
def add_attachment(plan_id, filename, b64content, **kwargs):
    """
    .. function:: RPC TestPlan.add_attachment(plan_id, filename, b64content)

        Add attachment to the given TestPlan.

        :param plan_id: PK of TestPlan
        :type plan_id: int
        :param filename: File name of attachment, e.g. 'logs.txt'
        :type filename: str
        :param b64content: Base64 encoded content
        :type b64content: str
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
    """
    attachment_dao.add_attachment(
        plan_id,
        "testplans.TestPlan",
        kwargs.get(REQUEST_KEY).user,
        filename,
        b64content,
    )


@permissions_required("testplans.view_testplan")
@rpc_method(name="TestPlan.tree")
def tree(plan_id):
    """
    .. function:: RPC TestPlan.tree(plan_id)

        Returns a list of the ancestry tree for the given TestPlan
        in a depth-first order!

        :param plan_id: PK of TestPlan to inspect
        :type plan_id: int
        :return: A DFS ordered list of all test plans in the family tree
                 starting from the root of the tree
        :rtype: list
        :raises TestPlan.DoesNotExit: if object specified by PK is missing
    """
    plan = test_plan_dao.get_by_id(plan_id)
    return test_plan_dao.tree(plan)
