# -*- coding: utf-8 -*-

from django.core.exceptions import ObjectDoesNotExist
from django.forms import EmailField, ValidationError

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.core.utils import string_to_list, form_errors_to_list
from tcms.core.utils.timedelta2int import timedelta2int
from tcms.management.models import TestTag
from tcms.management.models import Component
from tcms.testcases.models import TestCase

from tcms.xmlrpc.utils import pre_process_ids, pre_process_estimated_time
from tcms.xmlrpc.decorators import permissions_required


__all__ = (
    'add_component',
    'get_components',
    'remove_component',

    'add_notification_cc',
    'get_notification_cc',
    'remove_notification_cc',

    'add_tag',
    'attach_bug',
    'create',
    'detach_bug',
    'filter',
    'get',
    'get_bugs',
    'get_tags',
    'get_text',
    'remove_tag',
    'store_text',
    'update',
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
    Description: Creates a new Test Case object and stores it in the database.

    Params:      $values - Array/Hash: A reference to a hash or array of hashes with keys and values
                 matching the fields of the test case to be created.
      +----------------------------+----------------+-----------+----------------------------+
      | Field                      | Type           | Null      | Description                |
      +----------------------------+----------------+-----------+----------------------------+
      | product                    | Integer        | Required  | ID of Product              |
      | category                   | Integer        | Required  | ID of Category             |
      | priority                   | Integer        | Required  | ID of Priority             |
      | summary                    | String         | Required  |                            |
      | case_status                | Integer        | Optional  | ID of case status          |
      | plan                       | Array/Str/Int  | Optional  | ID or List of plan_ids     |
      | component                  | Integer/String | Optional  | ID of Priority             |
      | default_tester             | String         | Optional  | Login of tester            |
      | estimated_time             | String         | Optional  | 2h30m30s(recommend)        |
      |                            |                |           |  or HH:MM:SS Format        |
      | is_automated               | Integer        | Optional  | 0: Manual, 1: Auto, 2: Both|
      | is_automated_proposed      | Boolean        | Optional  | Default 0                  |
      | script                     | String         | Optional  |                            |
      | arguments                  | String         | Optional  |                            |
      | requirement                | String         | Optional  |                            |
      | alias                      | String         | Optional  | Must be unique             |
      | action                     | String         | Optional  |                            |
      | effect                     | String         | Optional  | Expected Result            |
      | setup                      | String         | Optional  |                            |
      | breakdown                  | String         | Optional  |                            |
      | tag                        | Array/String   | Optional  | String Comma separated     |
      | bug                        | Array/String   | Optional  | String Comma separated     |
      | extra_link                 | String         | Optional  | reference link             |
      +----------------------------+----------------+-----------+----------------------------+

    Returns: Array/Hash: The newly created object hash if a single case was created, or
             an array of objects if more than one was created. If any single case
             threw an error during creation, a hash with an ERROR key will be set in its place.

    Example:
    # Minimal test case parameters
    >>> values = {
        'category': 135,
        'product': 61,
        'summary': 'Testing XML-RPC',
        'priority': 1,
    }
    >>> TestCase.create(values)
    """
    from tcms.xmlrpc.forms import NewCaseForm

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

    return get(tc.case_id)


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
    Description: Performs a search and returns the resulting list of test cases.

    Params:      $query - Hash: keys must match valid search fields.

        +------------------------------------------------------------------+
        |                 Case Search Parameters                           |
        +------------------------------------------------------------------+
        |        Key          |          Valid Values                      |
        | author              | A bugzilla login (email address)           |
        | alias               | String                                     |
        | case_id             | Integer                                    |
        | case_status         | ForeignKey: Case Stat                      |
        | category            | ForeignKey: Category                       |
        | component           | ForeignKey: Component                      |
        | default_tester      | ForeignKey: Auth.User                      |
        | estimated_time      | String: 2h30m30s(recommend) or HH:MM:SS    |
        | plan                | ForeignKey: Test Plan                      |
        | priority            | ForeignKey: Priority                       |
        | category__product   | ForeignKey: Product                        |
        | summary             | String                                     |
        | tags                | ForeignKey: Tags                           |
        | create_date         | Datetime                                   |
        | is_automated        | 1: Only show current 0: show not current   |
        | script              | Text                                       |
        +------------------------------------------------------------------+

    Returns:     Array: Matching test cases are retuned in a list of hashes.

    Example:
    # Get all of cases contain 'TCMS' in summary
    >>> TestCase.filter({'summary__icontain': 'TCMS'})
    # Get all of cases create by xkuang
    >>> TestCase.filter({'author__username': 'xkuang'})
    # Get all of cases the author name starts with x
    >>> TestCase.filter({'author__username__startswith': 'x'})
    # Get all of cases belong to the plan 137
    >>> TestCase.filter({'plan__plan_id': 137})
    # Get all of cases belong to the plan create by xkuang
    >>> TestCase.filter({'plan__author__username': 'xkuang'})
    # Get cases with ID 12345, 23456, 34567 - Here is only support array so far.
    >>> TestCase.filter({'case_id__in': [12345, 23456, 34567]})
    """
    if query.get('estimated_time'):
        query['estimated_time'] = timedelta2int(
            pre_process_estimated_time(query.get('estimated_time'))
        )

    return TestCase.to_xmlrpc(query)


@rpc_method(name='TestCase.get')
def get(case_id):
    """
    Description: Used to load an existing test case from the database.

    Params:      $id - Integer/String: An integer representing the ID in the database

    Returns:     A blessed TestCase object Hash

    Example:
    >>> TestCase.get(1193)
    """
    test_case = TestCase.objects.get(case_id=case_id)

    test_case_latest_text = test_case.latest_text().serialize()

    response = test_case.serialize()
    response['text'] = test_case_latest_text
    # get the xmlrpc tags
    tag_ids = test_case.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    tags = TestTag.to_xmlrpc(query)
    # cut 'id' attribute off, only leave 'name' here
    tags_without_id = [x["name"] for x in tags]
    # replace tag_id list in the serialize return data
    response["tag"] = tags_without_id
    return response


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


@rpc_method(name='TestCase.get_text')
def get_text(case_id, case_text_version=None):
    """
    Description: The associated large text fields: Action, Expected Results, Setup, Breakdown
                 for a given version.

    Params:      $case_id - Integer/String: An integer representing the ID in the database

                 $version - Integer: (OPTIONAL) The version of the text you want returned.
                            Defaults to the latest.

    Returns:     Hash: case text object hash.

    Example:
    # Get all latest case text
    >>> TestCase.get_text(12345)
    # Get all case text with version 4
    >>> TestCase.get_text(12345, 4)
    """
    test_case = TestCase.objects.get(case_id=case_id)

    return test_case.get_text_with_version(
        case_text_version=case_text_version).serialize()


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

    return


@permissions_required('testcases.add_testcasetext')
@rpc_method(name='TestCase.store_text')
def store_text(case_id, action, **kwargs):
    """
    Description: Update the large text fields of a case.

    Params:    $case_id - Integer: An integer or alias representing the ID in the database.
               $action, $effect, $setup, $breakdown - String: Text for these fields.
               [$author_id] = Integer/String: (OPTIONAL) The numeric ID or the login of the author.
                              Defaults to logged in user

    Returns:     Hash: case text object hash.

    Example:
    # Minimal
    >>> TestCase.store_text(12345, 'Action')
    # Full arguments
    >>> TestCase.store_text(12345, 'Action', 'Effect', 'Setup', 'Breakdown', 2260)
    """
    from django.contrib.auth.models import User

    test_case = TestCase.objects.get(case_id=case_id)

    effect = kwargs.get('effect', '')
    setup = kwargs.get('setup', '')
    breakdown = kwargs.get('breakdown', '')
    author_id = kwargs.get('author_id', None)
    if author_id:
        author = User.objects.get(id=author_id)
    else:
        request = kwargs.get(REQUEST_KEY)
        author = request.user

    return test_case.add_text(
        author=author,
        action=action and action.strip(),
        effect=effect and effect.strip(),
        setup=setup and setup.strip(),
        breakdown=breakdown and breakdown.strip(),
    ).serialize()


@permissions_required('testcases.change_testcase')
@rpc_method(name='TestCase.update')
def update(case_ids, values):
    """
    Description: Updates the fields of the selected case or cases.

    Params:      $case_ids - Integer/String/Array
                             Integer: A single TestCase ID.
                             String:  A comma separates string of TestCase IDs for batch
                                      processing.
                             Array:   An array of case IDs for batch mode processing

                 $values   - Hash of keys matching TestCase fields and the new values
                             to set each field to.

    Returns:  Array: an array of case hashes. If the update on any particular
                     case failed, the has will contain a ERROR key and the
                     message as to why it failed.
        +-----------------------+----------------+-----------------------------------------+
        | Field                 | Type           | Null                                    |
        +-----------------------+----------------+-----------------------------------------+
        | case_status           | Integer        | Optional                                |
        | product               | Integer        | Optional(Required if changes category)  |
        | category              | Integer        | Optional                                |
        | priority              | Integer        | Optional                                |
        | default_tester        | String/Integer | Optional(str - user_name, int - user_id)|
        | estimated_time        | String         | Optional(2h30m30s(recommend) or HH:MM:SS|
        | is_automated          | Integer        | Optional(0 - Manual, 1 - Auto, 2 - Both)|
        | is_automated_proposed | Boolean        | Optional                                |
        | script                | String         | Optional                                |
        | arguments             | String         | Optional                                |
        | summary               | String         | Optional                                |
        | requirement           | String         | Optional                                |
        | alias                 | String         | Optional                                |
        | notes                 | String         | Optional                                |
        | extra_link            | String         | Optional(reference link)
        +-----------------------+----------------+-----------------------------------------+

    Example:
    # Update alias to 'tcms' for case 12345 and 23456
    >>> TestCase.update([12345, 23456], {'alias': 'tcms'})
    """
    from tcms.xmlrpc.forms import UpdateCaseForm

    if values.get('estimated_time'):
        values['estimated_time'] = pre_process_estimated_time(values.get('estimated_time'))

    form = UpdateCaseForm(values)

    if values.get('category') and not values.get('product'):
        raise ValueError('Product ID is required for category')

    if values.get('product'):
        form.populate(product_id=values['product'])

    if form.is_valid():
        tcs = TestCase.update(
            case_ids=pre_process_ids(value=case_ids),
            values=form.cleaned_data,
        )
    else:
        raise ValueError(form_errors_to_list(form))

    query = {'pk__in': tcs.values_list('pk', flat=True)}
    return TestCase.to_xmlrpc(query)
