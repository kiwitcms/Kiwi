# -*- coding: utf-8 -*-

from django.core.exceptions import ObjectDoesNotExist
from django.forms import EmailField, ValidationError

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.core.utils import string_to_list, form_errors_to_list
from tcms.core.utils.timedelta2int import timedelta2int
from tcms.management.models import TestTag
from tcms.management.models import Component
from tcms.testcases.models import TestCase
from tcms.xmlrpc.forms import UpdateCaseForm, NewCaseForm

from tcms.xmlrpc.utils import pre_process_ids, pre_process_estimated_time
from tcms.xmlrpc.decorators import permissions_required


__all__ = (
    'add_component',
    'get_components',
    'remove_component',

    'add_notification_cc',
    'get_notification_cc',
    'remove_notification_cc',

    'filter',
    'create',
    'update',

    'add_tag',
    'attach_bug',
    'detach_bug',
    'get_bugs',
    'get_tags',
    'remove_tag',
)


@permissions_required('testcases.add_testcasecomponent')
@rpc_method(name='TestCase.add_component')
def add_component(case_id, component_id):
    """
    .. function:: XML-RPC TestCase.add_component(case_id, component_id)

        Add component to the selected test case.

        :param case_id: PK of TestCase to modify
        :type case_id: int
        :param component_id: PK of Component to add
        :type component_id: int
        :return: None
        :raises: PermissionDenied if missing the *testcases.add_testcasecomponent*
                 permission
        :raises: DoesNotExist if missing test case or component that match the
                 specified PKs
    """
    TestCase.objects.get(pk=case_id).add_component(
        Component.objects.get(pk=component_id)
    )


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
    test_case = TestCase.objects.get(case_id=case_id)

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
    '''
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
    '''

    _validate_cc_list(cc_list)

    tc = TestCase.objects.get(pk=case_id)

    # First, find those that do not exist yet.
    existing_cc = tc.emailing.get_cc_list()
    adding_cc = list(set(cc_list) - set(existing_cc))

    # add the ones which are new
    tc.emailing.add_cc(adding_cc)


@permissions_required('testcases.change_testcase')
@rpc_method(name='TestCase.remove_notification_cc')
def remove_notification_cc(case_id, cc_list):
    '''
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
    '''

    _validate_cc_list(cc_list)

    TestCase.objects.get(pk=case_id).emailing.remove_cc(cc_list)


@rpc_method(name='TestCase.get_notification_cc')
def get_notification_cc(case_id):
    '''
    .. function:: XML-RPC TestCase.get_notification_cc(case_id)

        Return notification list for specified TestCase

        :param case_id: PK of TestCase
        :type case_id: int
        :return: List of email addresses
        :rtype: list(str)
        :raises: TestCase.DoesNotExist if object with case_id doesn't exist
    '''
    return TestCase.objects.get(pk=case_id).get_cc_list()


@permissions_required('testcases.add_testcasetag')
@rpc_method(name='TestCase.add_tag')
def add_tag(case_ids, tags):
    """
    Description: Add one or more tags to the selected test cases.

    Params:     $case_ids - Integer/Array/String: An integer representing the ID in the database,
                            an array of case_ids, or a string of comma separated case_ids.

                $tags - String/Array - A single tag, an array of tags,
                        or a comma separated list of tags.

    Returns:    Array: empty on success or an array of hashes with failure
                       codes if a failure occured.

    Example:
    # Add tag 'foobar' to case 1234
    >>> TestCase.add_tag(1234, 'foobar')
    # Add tag list ['foo', 'bar'] to cases list [12345, 67890]
    >>> TestCase.add_tag([12345, 67890], ['foo', 'bar'])
    # Add tag list ['foo', 'bar'] to cases list [12345, 67890] with String
    >>> TestCase.add_tag('12345, 67890', 'foo, bar')
    """
    tcs = TestCase.objects.filter(
        case_id__in=pre_process_ids(value=case_ids))

    tags = string_to_list(tags)

    for tag in tags:
        t, c = TestTag.objects.get_or_create(name=tag)
        for tc in tcs.iterator():
            tc.add_tag(tag=t)

    return


@permissions_required('testcases.add_testcasebug')
@rpc_method(name='TestCase.attach_bug')
def attach_bug(values):
    """
    Description: Add one or more bugs to the selected test cases.

    Params:     $values - Array/Hash: A reference to a hash or array of hashes with keys and values
                                      matching the fields of the test case bug to be created.

      +-------------------+----------------+-----------+-------------------------------+
      | Field             | Type           | Null      | Description                   |
      +-------------------+----------------+-----------+-------------------------------+
      | case_id           | Integer        | Required  | ID of Case                    |
      | bug_id            | Integer        | Required  | ID of Bug                     |
      | bug_system_id     | Integer        | Required  | ID of Bug tracker in DB       |
      | summary           | String         | Optional  | Bug summary                   |
      | description       | String         | Optional  | Bug description               |
      +-------------------+----------------+-----------+-------------------------------+

    Returns:     Array: empty on success or an array of hashes with failure
                 codes if a failure occured.

    Example:
    >>> TestCase.attach_bug({
        'case_id': 12345,
        'bug_id': 67890,
        'bug_system_id': 1,
        'summary': 'Testing TCMS',
        'description': 'Just foo and bar',
    })
    """
    from tcms.xmlrpc.forms import AttachCaseBugForm

    if isinstance(values, dict):
        values = [values, ]

    for value in values:
        form = AttachCaseBugForm(value)
        if form.is_valid():
            tc = TestCase.objects.only('pk').get(case_id=form.cleaned_data[
                'case_id'])
            tc.add_bug(
                bug_id=form.cleaned_data['bug_id'],
                bug_system_id=form.cleaned_data['bug_system_id'],
                summary=form.cleaned_data['summary'],
                description=form.cleaned_data['description']
            )
        else:
            raise ValueError(form_errors_to_list(form))
    return


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

    if not (values.get('category') or values.get('summary')):
        raise ValueError()

    values['component'] = pre_process_ids(values.get('component', []))
    values['plan'] = pre_process_ids(values.get('plan', []))
    values['bug'] = pre_process_ids(values.get('bug', []))
    if values.get('estimated_time'):
        values['estimated_time'] = pre_process_estimated_time(values.get('estimated_time'))

    form = NewCaseForm(values)
    form.populate(values.get('product'))

    if form.is_valid():
        # Create the case
        tc = TestCase.create(author=request.user, values=form.cleaned_data)

        # Add case text to the case
        tc.add_text(
            action=form.cleaned_data['action'] or '',
            effect=form.cleaned_data['effect'] or '',
            setup=form.cleaned_data['setup'] or '',
            breakdown=form.cleaned_data['breakdown'] or '',
        )

        # Add the case to specific plans
        for p in form.cleaned_data['plan']:
            tc.add_to_plan(plan=p)
            del p

        # Add components to the case
        for c in form.cleaned_data['component']:
            tc.add_component(component=c)
            del c

        # Add tag to the case
        for tag in string_to_list(values.get('tag', [])):
            t, c = TestTag.objects.get_or_create(name=tag)
            tc.add_tag(tag=t)
    else:
        # Print the errors if the form is not passed validation.
        raise ValueError(form_errors_to_list(form))

    result = tc.serialize()
    result['text'] = tc.latest_text().serialize()

    return result


@permissions_required('testcases.delete_testcasebug')
@rpc_method(name='TestCase.detach_bug')
def detach_bug(case_ids, bug_ids):
    """
    Description: Remove one or more bugs to the selected test cases.

    Params: $case_ids - Integer/Array/String: An integer representing the ID in the database,
                          an array of case_ids, or a string of comma separated case_ids
            $bug_ids - Integer/Array/String: An integer representing the ID in the database,
                        an array of bug_ids, or a string of comma separated primary key of bug_ids.

    Returns:     Array: empty on success or an array of hashes with failure
                 codes if a failure occured.

    Example:
    # Remove bug id 54321 from case 1234
    >>> TestCase.detach_bug(1234, 54321)
    # Remove bug ids list [1234, 5678] from cases list [56789, 12345]
    >>> TestCase.detach_bug([56789, 12345], [1234, 5678])
    # Remove bug ids list '1234, 5678' from cases list '56789, 12345' with String
    >>> TestCase.detach_bug('56789, 12345', '1234, 5678')
    """
    case_ids = pre_process_ids(case_ids)
    bug_ids = pre_process_ids(bug_ids)

    tcs = TestCase.objects.filter(case_id__in=case_ids).iterator()
    for tc in tcs:
        for opk in bug_ids:
            try:
                tc.remove_bug(bug_id=opk)
            except ObjectDoesNotExist:
                pass


@rpc_method(name='TestCase.filter')
def filter(query):
    """
    .. function:: XML-RPC TestCase.filter(query)

        Perform a search and return the resulting list of test cases
        augmented with their latest ``text``.

        :param query: Field lookups for :class:`tcms.testcases.models.TestCase`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.TestCase` objects.
                 The key ``text`` holds a the latest version of a serialized
                 :class:`tcms.testcases.models.TestCaseText` object!
        :rtype: list(dict)
    """
    if query.get('estimated_time'):
        query['estimated_time'] = timedelta2int(
            pre_process_estimated_time(query.get('estimated_time'))
        )

    results = []
    for case in TestCase.objects.filter(**query):
        serialized_case = case.serialize()
        serialized_case['text'] = case.latest_text().serialize()
        results.append(serialized_case)

    return results


@rpc_method(name='TestCase.get_bugs')
def get_bugs(case_ids):
    """
    Description: Get the list of bugs that are associated with this test case.

    Params:      $case_ids - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of bug object hashes.

    Example:
    # Get bugs belong to ID 12345
    >>> TestCase.get_bugs(12345)
    # Get bug belong to case ids list [12456, 23456]
    >>> TestCase.get_bugs([12456, 23456])
    # Get bug belong to case ids list 12456 and 23456 with string
    >>> TestCase.get_bugs('12456, 23456')
    """
    from tcms.testcases.models import TestCaseBug

    tcs = TestCase.objects.filter(
        case_id__in=pre_process_ids(value=case_ids)
    )

    query = {'case__case_id__in': tcs.values_list('case_id', flat=True)}
    return TestCaseBug.to_xmlrpc(query)


@rpc_method(name='TestCase.get_tags')
def get_tags(case_id):
    """
    Description: Get the list of tags attached to this case.

    Params:      $case_id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of tag object hashes.

    Example:
    >>> TestCase.get_tags(12345)
    """
    test_case = TestCase.objects.get(case_id=case_id)

    tag_ids = test_case.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    return TestTag.to_xmlrpc(query)


@permissions_required('testcases.delete_testcasetag')
@rpc_method(name='TestCase.remove_tag')
def remove_tag(case_ids, tags):
    """
    Description: Remove a tag from a case.

    Params: $case_ids - Integer/Array/String: An integer or alias representing the ID
                         in the database, an array of case_ids,
                         or a string of comma separated case_ids.

            $tags - String/Array - A single or multiple tag to be removed.

    Returns: Array: Empty on success.

    Example:
    # Remove tag 'foo' from case 1234
    >>> TestCase.remove_tag(1234, 'foo')
    # Remove tag 'foo' and bar from cases list [56789, 12345]
    >>> TestCase.remove_tag([56789, 12345], ['foo', 'bar'])
    # Remove tag 'foo' and 'bar' from cases list '56789, 12345' with String
    >>> TestCase.remove_tag('56789, 12345', 'foo, bar')
    """
    test_cases = TestCase.objects.filter(
        case_id__in=pre_process_ids(value=case_ids)
    )
    test_tags = TestTag.objects.filter(
        name__in=string_to_list(tags)
    )

    for test_case in test_cases.iterator():
        for test_tag in test_tags.iterator():
            test_case.remove_tag(test_tag)


@permissions_required('testcases.change_testcase')
@rpc_method(name='TestCase.update')
def update(case_id, values, **kwargs):
    """
    .. function:: XML-RPC TestCase.update(case_id, values)

        Update the fields of the selected test case.

        :param case_id: PK of TestCase to be modified
        :type case_id: int
        :param values: Field values for :class:`tcms.testcases.models.TestCase`.
                       The special keys ``setup``, ``breakdown``, ``action`` and
                       ``effect`` are recognized and will cause update of the underlying
                       :class:`tcms.testcases.models.TestCaseText` object!
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.TestCase` object
        :rtype: dict
        :raises: TestCase.DoesNotExist if object specified by PK doesn't exist
        :raises: PermissionDenied if missing *testcases.change_testcase* permission
    """
    if values.get('estimated_time'):
        values['estimated_time'] = pre_process_estimated_time(values.get('estimated_time'))

    form = UpdateCaseForm(values)

    if values.get('category') and not values.get('product'):
        raise ValueError('Product ID is required for category')

    if values.get('product'):
        form.populate(product_id=values['product'])

    if form.is_valid():
        tc = TestCase.objects.get(pk=case_id)
        for key in values.keys():
            # only modify attributes that were passed via parameters
            # skip attributes which are Many-to-Many relations
            if key not in ['component', 'tag'] and hasattr(tc, key):
                setattr(tc, key, form.cleaned_data[key])
        tc.save()

        # if we're updating the text if any one of these parameters was
        # specified
        if any(x in ['setup', 'action', 'effect', 'breakdown'] for x in values.keys()):
            action = form.cleaned_data.get('action', '').strip()
            effect = form.cleaned_data.get('effect', '').strip()
            setup = form.cleaned_data.get('setup', '').strip()
            breakdown = form.cleaned_data.get('breakdown', '').strip()
            author = kwargs.get(REQUEST_KEY).user

            tc.add_text(
                author=author,
                action=action,
                effect=effect,
                setup=setup,
                breakdown=breakdown,
            )
    else:
        raise ValueError(form_errors_to_list(form))

    return tc.serialize()
