# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.forms import EmailField, ValidationError
from django.forms.models import model_to_dict
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.dao.management.component_dao import component_dao
from tcms.dao.shared.attachment_dao import attachment_dao
from tcms.dao.shared.comment_dao import comment_dao
from tcms.dao.shared.property_dao import testcase_property_dao
from tcms.dao.shared.tag_dao import tag_dao
from tcms.dao.testcases.test_case_dao import test_case_dao
from tcms.rpc.api.forms.testcase import NewForm, UpdateForm
from tcms.rpc.decorators import permissions_required


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
    case = test_case_dao.get_by_id(case_id)
    component_obj = component_dao.get_by_name_and_product(component, case.category.product)
    return test_case_dao.add_component(case, component_obj)


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
    case = test_case_dao.get_by_id(case_id)
    test_case_dao.remove_component(case, component_dao.get_by_id(component_id))


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

    case = test_case_dao.get_by_id(case_id)
    test_case_dao.add_notification_cc(case, cc_list)


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

    case = test_case_dao.get_by_id(case_id)
    test_case_dao.remove_notification_cc(case, cc_list)


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
    case = test_case_dao.get_by_id(case_id)
    return test_case_dao.get_notification_cc(case)


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
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :raises PermissionDenied: if missing *testcases.add_testcasetag* permission
        :raises TestCase.DoesNotExist: if object specified by PK doesn't exist
        :raises Tag.DoesNotExist: if missing *management.add_tag* permission and *tag*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag_obj, _ = tag_dao.get_or_create(request.user, tag)
    case = test_case_dao.get_by_id(case_id)
    tag_dao.add_tag(case, tag_obj)


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
    tag_obj = tag_dao.get_by_name(tag)
    case = test_case_dao.get_by_id(case_id)
    tag_dao.remove_tag(case, tag_obj)


@permissions_required("testcases.add_testcase")
@rpc_method(name="TestCase.create")
def create(values, **kwargs):
    """
    .. function:: RPC TestCase.create(values)

        Create a new TestCase object and store it in the database.

        :param values: Field values for :class:`tcms.testcases.models.TestCase`
        :type values: dict
        :param \\**kwargs: Dict providing access to the current request, protocol,
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

        # auto_now_add will *always* set current date! see:
        # https://docs.djangoproject.com/en/6.0/ref/models/fields/#django.db.models.DateField.auto_now_add
        if "create_date" in form.cleaned_data:
            test_case.create_date = form.cleaned_data["create_date"]
            test_case.save()

        test_case_dao.save(test_case)
        result = model_to_dict(test_case, exclude=["component", "plan", "tag"])
        # b/c date is added in the DB layer and model_to_dict() doesn't return it
        result["create_date"] = test_case.create_date
        result["setup_duration"] = str(result["setup_duration"])
        result["testing_duration"] = str(result["testing_duration"])
        return result

    raise ValueError(list(form.errors.items()))


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

    return test_case_dao.filter(query)


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

    case = test_case_dao.get_by_id(case_id)
    return test_case_dao.history(case, query)


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

    return test_case_dao.sortkeys(query)


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
    test_case = test_case_dao.get_by_id(case_id)
    form = UpdateForm(values, instance=test_case)

    if form.is_valid():
        test_case = form.save()
        test_case_dao.save(test_case)
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
        result["setup_duration"] = str(result["setup_duration"])
        result["testing_duration"] = str(result["testing_duration"])

        return result

    raise ValueError(list(form.errors.items()))


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
    return test_case_dao.remove(query)


@permissions_required("attachments.view_attachment")
@rpc_method(name="TestCase.list_attachments")
def list_attachments(case_id, **kwargs):
    """
    .. function:: RPC TestCase.list_attachments(case_id)

        List attachments for the given TestCase.

        :param case_id: PK of TestCase to inspect
        :type case_id: int
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: A list containing information and download URLs for attachements
        :rtype: list
        :raises TestCase.DoesNotExist: if object specified by PK is missing
    """
    case = test_case_dao.get_by_id(case_id)
    request = kwargs.get(REQUEST_KEY)
    return attachment_dao.list_attachments(request, case)


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
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
    """
    attachment_dao.add_attachment(
        case_id,
        "testcases.TestCase",
        kwargs.get(REQUEST_KEY).user,
        filename,
        b64content,
    )


@permissions_required("django_comments.add_comment")
@rpc_method(name="TestCase.add_comment")
def add_comment(case_id, comment, user_id=None, submit_date=None, **kwargs):
    """
    .. function:: TestCase.add_comment(case_id, comment)

        Add comment to selected test case.

        :param case_id: PK of a TestCase object
        :type case_id: int
        :param comment: The text to add as a comment
        :type comment: str
        :param user_id: Override comment ``user`` field. Only super-user can use this!
        :type user_id: int
        :param submit_date: Override comment ``submit_date`` field. Only super-user can use this!
        :type submit_date: datetime.datetime
        :param \\**kwargs: Dict providing access to the current request, protocol,
                entry point name and handler instance from the rpc method
        :return: Serialized :class:`django_comments.models.Comment` object
        :rtype: dict
        :raises PermissionDenied: if missing *django_comments.add_comment* permission
        :raises TestCase.DoesNotExist: if object specified by PK is missing

        .. important::

            In webUI comments are only shown **only** during test case review!
    """
    case = test_case_dao.get_by_id(case_id)

    request_user = kwargs.get(REQUEST_KEY).user

    comment_author = request_user
    if user_id and request_user.is_superuser:
        comment_author = get_user_model().objects.get(pk=user_id)

    # only super-user can override this
    if not request_user.is_superuser:
        submit_date = None

    return comment_dao.add_comment(case, comment, comment_author, submit_date)


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
    case = test_case_dao.get_by_id(case_id)
    comment_dao.remove_comment(case, comment_id)


@permissions_required("django_comments.view_comment")
@rpc_method(name="TestCase.comments")
def comments(case_id):
    """
    .. function:: TestCase.comments(case_id)

        Return all comment(s) for the specified test case.

        :param case_id: PK of a TestCase object
        :type case_id: int
        :return: Serialized list of :class:`django_comments.models.Comment` objects
        :rtype: list(dict)
        :raises PermissionDenied: if missing *django_comments.view_comment* permission
        :raises TestCase.DoesNotExist: if object specified by PK is missing
    """
    case = test_case_dao.get_by_id(case_id)
    return comment_dao.get_comments(case)


@permissions_required("testcases.view_property")
@rpc_method(name="TestCase.properties")
def properties(query=None):
    """
    .. function:: TestCase.properties(query)

        Return all properties for the specified test case(s).

        :param query: Field lookups for :class:`tcms.testcases.models.Property`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.Property` objects.
        :rtype: list(dict)
        :raises PermissionDenied: if missing *testcases.view_property* permission
    """
    if query is None:
        query = {}

    return testcase_property_dao.filter(
        query,
        value_fields=("id", "case", "name", "value"),
        order_by=("case", "name", "value"),
    )


@permissions_required("testcases.delete_property")
@rpc_method(name="TestCase.remove_property")
def remove_property(query):
    """
    .. function:: TestCase.remove_property(query)

        Remove selected properties.

        :param query: Field lookups for :class:`tcms.testcases.models.Property`
        :type query: dict
        :raises PermissionDenied: if missing *testcases.delete_property* permission
    """
    testcase_property_dao.remove(query)


@permissions_required("testcases.add_property")
@rpc_method(name="TestCase.add_property")
def add_property(case_id, name, value):
    """
    .. function:: TestCase.add_property(case_id, name, value)

        Add property to test case! Duplicates are skipped without errors.

        :param case_id: Primary key for :class:`tcms.testcases.models.TestCase`
        :type case_id: int
        :param name: Name of the property
        :type name: str
        :param value: Value of the property
        :type value: str
        :return: Serialized :class:`tcms.testcases.models.Property` object.
        :rtype: dict
        :raises PermissionDenied: if missing *testcases.add_property* permission
    """
    return testcase_property_dao.get_or_create(case_id, name, value)
