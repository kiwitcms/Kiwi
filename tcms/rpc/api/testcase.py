# -*- coding: utf-8 -*-

from django.forms import EmailField, ValidationError
from modernrpc.core import REQUEST_KEY, rpc_method

from tcms.core.helpers import comments
from tcms.core.utils import form_errors_to_list
from tcms.management.models import Component, Tag
from tcms.rpc import utils
from tcms.rpc.api.forms.testcase import NewForm, UpdateForm
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import TestCase

__all__ = (
    'create',
    'update',
    'filter',
    'remove',

    'add_comment',
    'remove_comment',

    'add_component',
    'get_components',
    'remove_component',

    'add_notification_cc',
    'get_notification_cc',
    'remove_notification_cc',

    'add_tag',
    'remove_tag',

    'add_attachment',
    'list_attachments',
)


@permissions_required('testcases.add_testcasecomponent')
@rpc_method(name='TestCase.add_component')
def add_component(case_id, component):
    """
    .. function:: XML-RPC TestCase.add_component(case_id, component_id)

        Add component to the selected test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param component: Name of Component to add
        :type component_id: str
        :return: Serialized :class:`tcms.testcases.models.TestCase` object
        :raises: PermissionDenied if missing the *testcases.add_testcasecomponent*
                 permission
        :raises: DoesNotExist if missing test case or component that match the
                 specified PKs
    """
    case = TestCase.objects.get(pk=case_id)
    case.add_component(
        Component.objects.get(name=component, product=case.category.product)
    )
    return case.serialize()


@rpc_method(name='TestCase.get_components')
def get_components(case_id):
    """
    .. function:: XML-RPC TestCase.get_components(case_id)

        Get the list of components attached to this case.

        :param case_id: PK if TestCase
        :type case_id: int
        :return: Serialized list of :class:`tcms.management.models.Component` objects
        :rtype: list(dict)
        :raises: TestCase.DoesNotExist if missing test case matching PK
    """
    test_case = TestCase.objects.get(pk=case_id)

    component_ids = test_case.component.values_list('id', flat=True)
    query = {'id__in': component_ids}
    return Component.to_xmlrpc(query)


@permissions_required('testcases.delete_testcasecomponent')
@rpc_method(name='TestCase.remove_component')
def remove_component(case_id, component_id):
    """
    .. function:: XML-RPC TestCase.remove_component(case_id, component_id)

        Remove selected component from the selected test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param component_id: PK of Component to remove
        :type component_id: int
        :return: None
        :raises: PermissionDenied if missing the *testcases.delete_testcasecomponent*
                 permission
        :raises: DoesNotExist if missing test case or component that match the
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
        :return: None
        :raises: TypeError or ValidationError if addresses are not valid.
    """

    if not isinstance(cc_list, list):
        raise TypeError('cc_list should be a list object.')

    field = EmailField(required=True)
    invalid_emails = []

    for item in cc_list:
        try:
            field.clean(item)
        except ValidationError:
            invalid_emails.append(item)

    if invalid_emails:
        raise ValidationError(
            field.error_messages['invalid'] % {
                'value': ', '.join(invalid_emails)})


@permissions_required('testcases.change_testcase')
@rpc_method(name='TestCase.add_notification_cc')
def add_notification_cc(case_id, cc_list):
    """
    .. function:: XML-RPC TestCase.add_notification_cc(case_id, cc_list)

        Add email addresses to the notification list of specified TestCase

        :param case_id: PK of TestCase to be modified
        :param case_id: int
        :param cc_list: List of email addresses
        :type cc_list: list(str)
        :return: None
        :raises: TypeError or ValidationError if email validation fails
        :raises: PermissionDenied if missing *testcases.change_testcase* permission
        :raises: TestCase.DoesNotExist if object with case_id doesn't exist
    """

    _validate_cc_list(cc_list)

    test_case = TestCase.objects.get(pk=case_id)
    test_case.emailing.add_cc(cc_list)


@permissions_required('testcases.change_testcase')
@rpc_method(name='TestCase.remove_notification_cc')
def remove_notification_cc(case_id, cc_list):
    """
    .. function:: XML-RPC TestCase.remove_notification_cc(case_id, cc_list)

        Remove email addresses from the notification list of specified TestCase

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param cc_list: List of email addresses
        :type cc_list: list(str)
        :return: None
        :raises: TypeError or ValidationError if email validation fails
        :raises: PermissionDenied if missing *testcases.change_testcase* permission
        :raises: TestCase.DoesNotExist if object with case_id doesn't exist
    """

    _validate_cc_list(cc_list)

    TestCase.objects.get(pk=case_id).emailing.remove_cc(cc_list)


@rpc_method(name='TestCase.get_notification_cc')
def get_notification_cc(case_id):
    """
    .. function:: XML-RPC TestCase.get_notification_cc(case_id)

        Return notification list for specified TestCase

        :param case_id: PK of TestCase
        :type case_id: int
        :return: List of email addresses
        :rtype: list(str)
        :raises: TestCase.DoesNotExist if object with case_id doesn't exist
    """
    return TestCase.objects.get(pk=case_id).get_cc_list()


@permissions_required('testcases.add_testcasetag')
@rpc_method(name='TestCase.add_tag')
def add_tag(case_id, tag, **kwargs):
    """
    .. function:: XML-RPC TestCase.add_tag(case_id, tag)

        Add one tag to the specified test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param tag: Tag name to add
        :type tag: str
        :return: None
        :raises: PermissionDenied if missing *testcases.add_testcasetag* permission
        :raises: TestCase.DoesNotExist if object specified by PK doesn't exist
        :raises: Tag.DoesNotExist if missing *management.add_tag* permission and *tag*
                 doesn't exist in the database!
    """
    request = kwargs.get(REQUEST_KEY)
    tag, _ = Tag.get_or_create(request.user, tag)
    TestCase.objects.get(pk=case_id).add_tag(tag)


@permissions_required('testcases.delete_testcasetag')
@rpc_method(name='TestCase.remove_tag')
def remove_tag(case_id, tag):
    """
    .. function:: XML-RPC TestCase.remove_tag(case_id, tag)

        Remove tag from a test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param tag: Tag name to remove
        :type tag: str
        :return: None
        :raises: PermissionDenied if missing *testcases.delete_testcasetag* permission
        :raises: DoesNotExist if objects specified don't exist
    """
    TestCase.objects.get(pk=case_id).remove_tag(
        Tag.objects.get(name=tag)
    )


@permissions_required('testcases.add_testcase')
@rpc_method(name='TestCase.create')
def create(values, **kwargs):
    """
    .. function:: XML-RPC TestCase.create(values)

        Create a new TestCase object and store it in the database.

        :param values: Field values for :class:`tcms.testcases.models.TestCase`
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.TestCase` object
        :rtype: dict
        :raises: PermissionDenied if missing *testcases.add_testcase* permission

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

    # b/c form was designed badly in the past clients send 'product'
    # as one of the fields. With the new forms product isn't accepted
    # but we add this as backward compatibility for older clients
    # otherwise they will start failing.
    # todo: remove after all clients have been updated
    if values.get('product'):
        del values['product']

    # todo: this is sent by junit-plugin while Python plugins use the above
    if values.get('product_id'):
        del values['product_id']

    if not (values.get('author') or values.get('author_id')):
        values['author'] = request.user.pk

    form = NewForm(values)

    if form.is_valid():
        test_case = form.save()
    else:
        raise ValueError(form_errors_to_list(form))

    return test_case.serialize()


@rpc_method(name='TestCase.filter')
def filter(query=None):  # pylint: disable=redefined-builtin
    """
    .. function:: XML-RPC TestCase.filter(query)

        Perform a search and return the resulting list of test cases
        augmented with their latest ``text``.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCase`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.TestCase` objects.
        :rtype: list(dict)
    """
    if query is None:
        query = {}

    return TestCase.to_xmlrpc(query)


@permissions_required('testcases.change_testcase')
@rpc_method(name='TestCase.update')
def update(case_id, values):
    """
    .. function:: XML-RPC TestCase.update(case_id, values)

        Update the fields of the selected test case.

        :param case_id: PK of TestCase to be modified
        :type case_id: int
        :param values: Field values for :class:`tcms.testcases.models.TestCase`.
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.TestCase` object
        :rtype: dict
        :raises: TestCase.DoesNotExist if object specified by PK doesn't exist
        :raises: PermissionDenied if missing *testcases.change_testcase* permission
    """
    test_case = TestCase.objects.get(pk=case_id)
    form = UpdateForm(values, instance=test_case)

    if form.is_valid():
        test_case = form.save()
    else:
        raise ValueError(form_errors_to_list(form))

    return test_case.serialize()


@permissions_required('testcases.delete_testcase')
@rpc_method(name='TestCase.remove')
def remove(query):
    """
    .. function:: XML-RPC TestCase.remove(query)

        Remove TestCase object(s).

        :param query: Field lookups for :class:`tcms.testcases.models.TestCase`
        :type query: dict
        :return: None
        :raises: PermissionDenied if missing the *testcases.delete_testcase* permission

        Example - removing bug from TestCase::

            >>> TestCase.remove({
                'pk__in': [1, 2, 3, 4],
            })
    """
    return TestCase.objects.filter(**query).delete()


@permissions_required('attachments.view_attachment')
@rpc_method(name='TestCase.list_attachments')
def list_attachments(case_id, **kwargs):
    """
    .. function:: XML-RPC TestCase.list_attachments(case_id)

        List attachments for the given TestCase.

        :param case_id: PK of TestCase to inspect
        :type case_id: int
        :return: A list containing information and download URLs for attachements
        :rtype: list
        :raises: TestCase.DoesNotExit if object specified by PK is missing
    """
    case = TestCase.objects.get(pk=case_id)
    request = kwargs.get(REQUEST_KEY)
    return utils.get_attachments_for(request, case)


@permissions_required('attachments.add_attachment')
@rpc_method(name='TestCase.add_attachment')
def add_attachment(case_id, filename, b64content, **kwargs):
    """
    .. function:: XML-RPC TestCase.add_attachment(case_id, filename, b64content)

        Add attachment to the given TestCase.

        :param case_id: PK of TestCase
        :type case_id: int
        :param filename: File name of attachment, e.g. 'logs.txt'
        :type filename: str
        :param b64content: Base64 encoded content
        :type b64content: str
        :return: None
    """
    utils.add_attachment(
        case_id,
        'testcases.TestCase',
        kwargs.get(REQUEST_KEY).user,
        filename,
        b64content)


@permissions_required('django_comments.add_comment')
@rpc_method(name='TestCase.add_comment')
def add_comment(case_id, comment, **kwargs):
    """
    .. function:: TestCase.add_comment(case_id, comment)

        Add comment to selected test case.

        :param case_id: PK of a TestCase object
        :param case_id: int
        :param comment: The text to add as a comment
        :param comment: str
        :return: None or JSON string in case of errors
        :raises: PermissionDenied if missing *django_comments.add_comment* permission

        .. important::

            In webUI comments are only shown **only** during test case review!
    """
    case = TestCase.objects.get(pk=case_id)
    comments.add_comment([case], comment, kwargs.get(REQUEST_KEY).user)


@permissions_required('django_comments.delete_comment')
@rpc_method(name='TestCase.remove_comment')
def remove_comment(case_id, comment_id=None):
    """
    .. function:: TestCase.remove_comment(case_id, comment_id)

        Remove all or specified comment(s) from selected test case.

        :param case_id: PK of a TestCase object
        :param case_id: int
        :param comment_id: PK of a Comment object or None
        :param comment_id: int
        :return: None
        :raises: PermissionDenied if missing *django_comments.delete_comment* permission
    """
    case = TestCase.objects.get(pk=case_id)
    to_be_deleted = comments.get_comments(case)
    if comment_id:
        to_be_deleted = to_be_deleted.filter(pk=comment_id)

    to_be_deleted.delete()
