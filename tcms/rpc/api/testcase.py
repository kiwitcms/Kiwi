# -*- coding: utf-8 -*-

from django.forms import EmailField, ValidationError
from django.forms.models import model_to_dict
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.core import helpers
from tcms.core.utils import form_errors_to_list
from tcms.management.models import Component, Tag
from tcms.rpc import utils
from tcms.rpc.api.forms.testcase import NewForm, UpdateForm
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import TestCase, TestCasePlan

__all__ = (
    "create",
    "update",
    "filter",
    "history",
    "sortkeys",
    "remove",
    "add_comment",
    "remove_comment",
    "add_component",
    "comments",
    "remove_component",
    "add_notification_cc",
    "get_notification_cc",
    "remove_notification_cc",
    "add_tag",
    "remove_tag",
    "add_attachment",
    "list_attachments",
)


@permissions_required("testcases.add_testcasecomponent")
@rpc_method(name="TestCase.add_component")
def add_component(case_id, component):
    """
    .. function:: RPC TestCase.add_component(case_id, component)

        Add component to the selected test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param component: Name of Component to add
        :type component: str
        :return: Serialized :class:`tcms.management.models.Component` object
        :rtype: dict
        :raises PermissionDenied: if missing the *testcases.add_testcasecomponent*
                 permission
        :raises DoesNotExist: if missing test case or component that match the
                 specified PKs
    """
    case = TestCase.objects.get(pk=case_id)
    component_obj = Component.objects.get(name=component, product=case.category.product)
    case.add_component(component_obj)
    return model_to_dict(component_obj)


@permissions_required("testcases.delete_testcasecomponent")
@rpc_method(name="TestCase.remove_component")
def remove_component(case_id, component_id):
    """
    .. function:: RPC TestCase.remove_component(case_id, component_id)

        Remove selected component from the selected test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param component_id: PK of Component to remove
        :type component_id: int
        :raises PermissionDenied: if missing the *testcases.delete_testcasecomponent*
                 permission
        :raises DoesNotExist: if missing test case or component that match the
                 specified PKs
    """
    TestCase.objects.get(pk=case_id).remove_component(
        Component.objects.get(pk=component_id)
    )


def _validate_cc_list(cc_list):
    """
    Validate each email address given in argument. Called by
    notification RPC methods.

    :param cc_list: List of email addresses
    :type cc_list: list
    :raises TypeError or ValidationError: if addresses are not valid.
    """

    if not isinstance(cc_list, list):
        raise TypeError("cc_list should be a list object.")

    field = EmailField(
        required=True,
        error_messages={"invalid": "Following email address(es) are invalid: %s"},
    )
    invalid_emails = []

    for item in cc_list:
        try:
            field.clean(item)
        except ValidationError:
            invalid_emails.append(item)

    if invalid_emails:
        raise ValidationError(
            field.error_messages["invalid"] % ", ".join(invalid_emails)
        )


@permissions_required("testcases.change_testcase")
@rpc_method(name="TestCase.add_notification_cc")
def add_notification_cc(case_id, cc_list):
    """
    .. function:: RPC TestCase.add_notification_cc(case_id, cc_list)

        Add email addresses to the notification list of specified TestCase

        :param case_id: PK of TestCase to be modified
        :type case_id: int
        :param cc_list: List of email addresses
        :type cc_list: list(str)
        :raises TypeError or ValidationError: if email validation fails
        :raises PermissionDenied: if missing *testcases.change_testcase* permission
        :raises TestCase.DoesNotExist: if object with case_id doesn't exist
    """

    _validate_cc_list(cc_list)

    test_case = TestCase.objects.get(pk=case_id)
    test_case.emailing.add_cc(cc_list)


@permissions_required("testcases.change_testcase")
@rpc_method(name="TestCase.remove_notification_cc")
def remove_notification_cc(case_id, cc_list):
    """
    .. function:: RPC TestCase.remove_notification_cc(case_id, cc_list)

        Remove email addresses from the notification list of specified TestCase

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param cc_list: List of email addresses
        :type cc_list: list(str)
        :raises TypeError or ValidationError: if email validation fails
        :raises PermissionDenied: if missing *testcases.change_testcase* permission
        :raises TestCase.DoesNotExist: if object with case_id doesn't exist
    """

    _validate_cc_list(cc_list)

    TestCase.objects.get(pk=case_id).emailing.remove_cc(cc_list)


@permissions_required("testcases.view_testcase")
@rpc_method(name="TestCase.get_notification_cc")
def get_notification_cc(case_id):
    """
    .. function:: RPC TestCase.get_notification_cc(case_id)

        Return notification list for specified TestCase

        :param case_id: PK of TestCase
        :type case_id: int
        :return: List of email addresses
        :rtype: list(str)
        :raises TestCase.DoesNotExist: if object with case_id doesn't exist
    """
    return TestCase.objects.get(pk=case_id).emailing.get_cc_list()


@permissions_required("testcases.add_testcasetag")
@rpc_method(name="TestCase.add_tag")
def add_tag(case_id, tag, **kwargs):
    """
    .. function:: RPC TestCase.add_tag(case_id, tag)

        Add one tag to the specified test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param tag: Tag name to add
        :type tag: str
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :raises PermissionDenied: if missing *testcases.add_testcasetag* permission
        :raises TestCase.DoesNotExist: if object specified by PK doesn't exist
        :raises Tag.DoesNotExist: if missing *management.add_tag* permission and *tag*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag, _ = Tag.get_or_create(request.user, tag)
    TestCase.objects.get(pk=case_id).add_tag(tag)


@permissions_required("testcases.delete_testcasetag")
@rpc_method(name="TestCase.remove_tag")
def remove_tag(case_id, tag):
    """
    .. function:: RPC TestCase.remove_tag(case_id, tag)

        Remove tag from a test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param tag: Tag name to remove
        :type tag: str
        :raises PermissionDenied: if missing *testcases.delete_testcasetag* permission
        :raises DoesNotExist: if objects specified don't exist
    """
    TestCase.objects.get(pk=case_id).remove_tag(Tag.objects.get(name=tag))


@permissions_required("testcases.add_testcase")
@rpc_method(name="TestCase.create")
def create(values, **kwargs):
    """
    .. function:: RPC TestCase.create(values)

        Create a new TestCase object and store it in the database.

        :param values: Field values for :class:`tcms.testcases.models.TestCase`
        :type values: dict
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`tcms.testcases.models.TestCase` object
        :rtype: dict
        :raises ValueError: if form is not valid
        :raises PermissionDenied: if missing *testcases.add_testcase* permission

        Minimal test case parameters::

            >>> values = {
                'category': 135,
                'product': 61,
            'summary': 'Testing XML-RPC',
            'priority': 1,
            }
            >>> TestCase.create(values)
    """
    request = kwargs.get(REQUEST_KEY)

    if not (values.get("author") or values.get("author_id")):
        values["author"] = request.user.pk

    form = NewForm(values)

    if form.is_valid():
        test_case = form.save()
        result = model_to_dict(test_case, exclude=["component", "plan", "tag"])
        # b/c date is added in the DB layer and model_to_dict() doesn't return it
        result["create_date"] = test_case.create_date
        return result

    raise ValueError(form_errors_to_list(form))


@permissions_required("testcases.view_testcase")
@rpc_method(name="TestCase.filter")
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC TestCase.filter(query)

        Perform a search and return the resulting list of test cases
        augmented with their latest ``text``.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCase`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.TestCase` objects.
        :rtype: list(dict)
    """
    if query is None:
        query = {}

    return list(
        TestCase.objects.filter(**query)
        .values(
            "id",
            "create_date",
            "is_automated",
            "script",
            "arguments",
            "extra_link",
            "summary",
            "requirement",
            "notes",
            "text",
            "case_status",
            "case_status__name",
            "category",
            "category__name",
            "priority",
            "priority__value",
            "author",
            "author__username",
            "default_tester",
            "default_tester__username",
            "reviewer",
            "reviewer__username",
        )
        .distinct()
    )


@permissions_required("testcases.view_testcase")
@rpc_method(name="TestCase.history")
def history(case_id, query=None):
    """
    .. function:: RPC TestCase.history(case_id, query)

        Return the history for a specified test case.

        :param case_id: TestCase PK
        :type case_id: int
        :param query: Field lookups for :class:`tcms.testcases.models.TestCase`
        :type query: dict
        :return: Serialized list of HistoricalTestCase objects.
        :rtype: list(dict)
    """
    if query is None:
        query = {}

    return list(TestCase.objects.get(pk=case_id).history.filter(**query).values())


@permissions_required("testcases.view_testcase")
@rpc_method(name="TestCase.sortkeys")
def sortkeys(query=None):
    """
    .. function:: RPC TestCase.sortkeys(query)

        Return information about TestCase position inside TestPlan.

        For example `TestCase.sortkeys({'plan': 3})`

        :param query: Field lookups for :class:`tcms.testcases.models.TestCasePlan`
        :type query: dict
        :return: Dictionary of (case_id, sortkey) pairs!
        :rtype: dict(case_id, sortkey)
    """
    if query is None:
        query = {}

    result = {}
    for record in TestCasePlan.objects.filter(**query):
        # NOTE: convert to str() otherwise we get:
        # Unable to serialize result as valid XML: dictionary key must be string
        result[str(record.case_id)] = record.sortkey

    return result


@permissions_required("testcases.change_testcase")
@rpc_method(name="TestCase.update")
def update(case_id, values):
    """
    .. function:: RPC TestCase.update(case_id, values)

        Update the fields of the selected test case.

        :param case_id: PK of TestCase to be modified
        :type case_id: int
        :param values: Field values for :class:`tcms.testcases.models.TestCase`.
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.TestCase` object
        :rtype: dict
        :raises ValueError: if form is not valid
        :raises TestCase.DoesNotExist: if object specified by PK doesn't exist
        :raises PermissionDenied: if missing *testcases.change_testcase* permission
    """
    test_case = TestCase.objects.get(pk=case_id)
    form = UpdateForm(values, instance=test_case)

    if form.is_valid():
        test_case = form.save()
        result = model_to_dict(test_case, exclude=["component", "plan", "tag"])
        # b/c date may be None and model_to_dict() doesn't return it
        result["create_date"] = test_case.create_date

        # additional information
        result["case_status__name"] = test_case.case_status.name
        result["category__name"] = test_case.category.name
        result["priority__value"] = test_case.priority.value
        result["author__username"] = (
            test_case.author.username if test_case.author else None
        )
        result["default_tester__username"] = (
            test_case.default_tester.username if test_case.default_tester else None
        )
        result["reviewer__username"] = (
            test_case.reviewer.username if test_case.reviewer else None
        )

        return result

    raise ValueError(form_errors_to_list(form))


@permissions_required("testcases.delete_testcase")
@rpc_method(name="TestCase.remove")
def remove(query):
    """
    .. function:: RPC TestCase.remove(query)

        Remove TestCase object(s).

        :param query: Field lookups for :class:`tcms.testcases.models.TestCase`
        :type query: dict
        :raises PermissionDenied: if missing the *testcases.delete_testcase* permission
        :return: The number of objects deleted and a dictionary with the
                 number of deletions per object type.
        :rtype: int, dict

        Example - removing bug from TestCase::

            >>> TestCase.remove({
                'pk__in': [1, 2, 3, 4],
            })
    """
    return TestCase.objects.filter(**query).delete()


@permissions_required("attachments.view_attachment")
@rpc_method(name="TestCase.list_attachments")
def list_attachments(case_id, **kwargs):
    """
    .. function:: RPC TestCase.list_attachments(case_id)

        List attachments for the given TestCase.

        :param case_id: PK of TestCase to inspect
        :type case_id: int
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: A list containing information and download URLs for attachements
        :rtype: list
        :raises TestCase.DoesNotExist: if object specified by PK is missing
    """
    case = TestCase.objects.get(pk=case_id)
    request = kwargs.get(REQUEST_KEY)
    return utils.get_attachments_for(request, case)


@permissions_required("attachments.add_attachment")
@rpc_method(name="TestCase.add_attachment")
def add_attachment(case_id, filename, b64content, **kwargs):
    """
    .. function:: RPC TestCase.add_attachment(case_id, filename, b64content)

        Add attachment to the given TestCase.

        :param case_id: PK of TestCase
        :type case_id: int
        :param filename: File name of attachment, e.g. 'logs.txt'
        :type filename: str
        :param b64content: Base64 encoded content
        :type b64content: str
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
    """
    utils.add_attachment(
        case_id,
        "testcases.TestCase",
        kwargs.get(REQUEST_KEY).user,
        filename,
        b64content,
    )


@permissions_required("django_comments.add_comment")
@rpc_method(name="TestCase.add_comment")
def add_comment(case_id, comment, **kwargs):
    """
    .. function:: TestCase.add_comment(case_id, comment)

        Add comment to selected test case.

        :param case_id: PK of a TestCase object
        :type case_id: int
        :param comment: The text to add as a comment
        :type comment: str
        :param kwargs: Dict providing access to the current request, protocol
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: dict
        :raises PermissionDenied: if missing *django_comments.add_comment* permission
        :raises TestCase.DoesNotExist: if object specified by PK is missing

        .. important::

            In webUI comments are only shown **only** during test case review!
    """
    case = TestCase.objects.get(pk=case_id)
    created = helpers.comments.add_comment(
        [case], comment, kwargs.get(REQUEST_KEY).user
    )
    # we always create only one comment
    return model_to_dict(created[0])


@permissions_required("django_comments.delete_comment")
@rpc_method(name="TestCase.remove_comment")
def remove_comment(case_id, comment_id=None):
    """
    .. function:: TestCase.remove_comment(case_id, comment_id)

        Remove all or specified comment(s) from selected test case.

        :param case_id: PK of a TestCase object
        :type case_id: int
        :param comment_id: PK of a Comment object or None
        :type comment_id: int
        :raises PermissionDenied: if missing *django_comments.delete_comment* permission
        :raises TestCase.DoesNotExist: if object specified by PK is missing
    """
    case = TestCase.objects.get(pk=case_id)
    to_be_deleted = helpers.comments.get_comments(case)
    if comment_id:
        to_be_deleted = to_be_deleted.filter(pk=comment_id)

    to_be_deleted.delete()


@permissions_required("django_comments.view_comment")
@rpc_method(name="TestCase.comments")
def comments(case_id):
    """
    .. function:: TestCase.comments(case_id)

        Return all comment(s) for the specified test case.

        :param case_id: PK of a TestCase object
        :type case_id: int
        :return: Serialized list of :class:`django_comments.models.Comment` objects
        :rtype: list
        :raises PermissionDenied: if missing *django_comments.view_comment* permission
        :raises TestCase.DoesNotExist: if object specified by PK is missing
    """
    case = TestCase.objects.get(pk=case_id)
    result = []
    for comment in helpers.comments.get_comments(case):
        result.append(model_to_dict(comment))

    return result
