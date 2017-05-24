# -*- coding: utf-8 -*-

from itertools import imap

from django.core.exceptions import ObjectDoesNotExist
from django.forms import EmailField, ValidationError

from kobo.django.xmlrpc.decorators import user_passes_test

from tcms.core.utils.timedelta2int import timedelta2int
from tcms.management.models import TestTag
from tcms.testcases.models import TestCase
from tcms.testcases.models import TestCasePlan
from tcms.testplans.models import TestPlan
from tcms.xmlrpc.decorators import log_call
from tcms.xmlrpc.utils import distinct_count
from tcms.xmlrpc.utils import pre_process_estimated_time
from tcms.xmlrpc.utils import pre_process_ids

__all__ = (
    'add_comment',
    'add_component',
    'add_tag',
    'add_to_run',
    'attach_bug',
    'check_case_status',
    'check_priority',
    'calculate_average_estimated_time',
    'calculate_total_estimated_time',
    'create',
    'detach_bug',
    'filter',
    'filter_count',
    'get',
    'get_bug_systems',
    'get_bugs',
    'get_case_run_history',
    'get_case_status',
    'get_change_history',
    'get_components',
    'get_plans',
    'get_tags',
    'get_text',
    'get_priority',
    'link_plan',
    'lookup_category_name_by_id',
    'lookup_category_id_by_name',
    'lookup_priority_name_by_id',
    'lookup_priority_id_by_name',
    'lookup_status_name_by_id',
    'lookup_status_id_by_name',
    'notification_add_cc',
    'notification_get_cc_list',
    'notification_remove_cc',
    'remove_component',
    'remove_tag',
    'store_text',
    'unlink_plan',
    'update',
)

__xmlrpc_namespace__ = 'TestCase'


@log_call(namespace=__xmlrpc_namespace__)
def add_comment(request, case_ids, comment):
    """
    Description: Adds comments to selected test cases.

    Params:      $case_ids - Integer/Array/String: An integer representing the ID in the database,
                             an array of case_ids, or a string of comma separated case_ids.

                 $comment - String - The comment

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occured.

    Example:
    # Add comment 'foobar' to case 1234
    >>> TestCase.add_comment(1234, 'foobar')
    # Add 'foobar' to cases list [56789, 12345]
    >>> TestCase.add_comment([56789, 12345], 'foobar')
    # Add 'foobar' to cases list '56789, 12345' with String
    >>> TestCase.add_comment('56789, 12345', 'foobar')
    """
    from tcms.xmlrpc.utils import Comment

    object_pks = pre_process_ids(value=case_ids)
    c = Comment(
        request=request,
        content_type='testcases.testcase',
        object_pks=object_pks,
        comment=comment
    )

    return c.add()


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.add_testcasecomponent'))
def add_component(request, case_ids, component_ids):
    """
    Description: Adds one or more components to the selected test cases.

    Params:      $case_ids - Integer/Array/String: An integer representing the ID in the database,
                             an array of case_ids, or a string of comma separated case_ids.

                 $component_ids - Integer/Array/String - The component ID, an array of Component IDs
                                  or a comma separated list of component IDs

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occured.

    Example:
    # Add component id 54321 to case 1234
    >>> TestCase.add_component(1234, 54321)
    # Add component ids list [1234, 5678] to cases list [56789, 12345]
    >>> TestCase.add_component([56789, 12345], [1234, 5678])
    # Add component ids list '1234, 5678' to cases list '56789, 12345' with String
    >>> TestCase.add_component('56789, 12345', '1234, 5678')
    """
    from tcms.management.models import Component

    tcs = TestCase.objects.filter(
        case_id__in=pre_process_ids(value=case_ids))
    cs = Component.objects.filter(
        id__in=pre_process_ids(value=component_ids))

    try:
        for tc in tcs.iterator():
            for c in cs.iterator():
                tc.add_component(component=c)
    except:
        raise

    return


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.add_testcasetag'))
def add_tag(request, case_ids, tags):
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

    tags = TestTag.string_to_list(tags)

    for tag in tags:
        t, c = TestTag.objects.get_or_create(name=tag)
        for tc in tcs.iterator():
            tc.add_tag(tag=t)

    return


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testruns.add_testcaserun'))
def add_to_run(request, case_ids, run_ids):
    """
    Description: Add one or more cases to the selected test runs.

    Params:      $case_ids - Integer/Array/String: An integer representing the ID in the database,
                             an array of case_ids, or a string of comma separated case_ids.

                 $run_ids - Integer/Array/String: An integer representing the ID in the database
                             an array of IDs, or a comma separated list of IDs.

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occured.

    Example:
    # Add case 1234 to run id 54321
    >>> TestCase.add_to_run(1234, 54321)
    # Add case ids list [56789, 12345] to run list [1234, 5678]
    >>> TestCase.add_to_run([56789, 12345], [1234, 5678])
    # Add case ids list 56789 and 12345 to run list 1234 and 5678 with String
    >>> TestCase.add_to_run('56789, 12345', '1234, 5678')
    """
    from tcms.testruns.models import TestRun

    case_ids = pre_process_ids(case_ids)
    run_ids = pre_process_ids(run_ids)

    trs = TestRun.objects.filter(run_id__in=run_ids)
    if not trs.exists():
        raise ValueError('Invalid run_ids')

    tcs = TestCase.objects.filter(case_id__in=case_ids)
    if not tcs.exists():
        raise ValueError('Invalid case_ids')

    for tr in trs.iterator():
        for tc in tcs.iterator():
            tr.add_case_run(case=tc)

    return


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.add_testcasebug'))
def attach_bug(request, values):
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
    from tcms.core import forms
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
            raise ValueError(forms.errors_to_list(form))
    return


@log_call(namespace=__xmlrpc_namespace__)
def check_case_status(request, name):
    """
    Description: Looks up and returns a case status by name.

    Params:      $name - String: name of the case status.

    Returns:     Hash: Matching case status object hash or error if not found.

    Example:
    >>> TestCase.check_case_status('proposed')
    """
    from tcms.testcases.models import TestCaseStatus

    return TestCaseStatus.objects.get(name=name).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def check_priority(request, value):
    """
    Description: Looks up and returns a priority by name.

    Params:      $value - String: name of the priority.

    Returns:     Hash: Matching priority object hash or error if not found.

    Example:
    >>> TestCase.check_priority('p1')
    """
    from tcms.management.models import Priority

    return Priority.objects.get(value=value).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def calculate_average_estimated_time(request, case_ids):
    """
    Description: Returns an average estimated time for cases.

    Params:      $case_ids - Integer/String: An integer representing the ID in the database.

    Returns:     String: Time in "HH:MM:SS" format.

    Example:
    >>> TestCase.calculate_average_time([609, 610, 611])
    """
    from django.db.models import Avg

    tcs = TestCase.objects.filter(
        pk__in=pre_process_ids(case_ids)).only('estimated_time')

    if not tcs.exists():
        raise ValueError('Please input valid case Id')

    # aggregate avg return integer directly rather than timedelta
    seconds = tcs.aggregate(Avg('estimated_time')).get('estimated_time__avg')

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    # TODO: return h:m:s or d:h:m
    return '%02i:%02i:%02i' % (h, m, s)


@log_call(namespace=__xmlrpc_namespace__)
def calculate_total_estimated_time(request, case_ids):
    """
    Description: Returns an total estimated time for cases.

    Params:      $case_ids - Integer/String: An integer representing the ID in the database.

    Returns:     String: Time in "HH:MM:SS" format.

    Example:
    >>> TestCase.calculate_total_time([609, 610, 611])
    """
    from django.db.models import Sum

    tcs = TestCase.objects.filter(
        pk__in=pre_process_ids(case_ids)).only('estimated_time')

    if not tcs.exists():
        raise ValueError('Please input valid case Id')

    # aggregate Sum return integer directly rather than timedelta
    seconds = tcs.aggregate(Sum('estimated_time')).get('estimated_time__sum')

    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    # TODO: return h:m:s or d:h:m
    return '%02i:%02i:%02i' % (h, m, s)


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.add_testcase'))
def create(request, values):
    """
    Description: Creates a new Test Case object and stores it in the database.

    Params:      $values - Array/Hash: A reference to a hash or array of hashes with keys and values
                 matching the fields of the test case to be created.
      +----------------------------+----------------+-----------+---------------------------------------+
      | Field                      | Type           | Null      | Description                           |
      +----------------------------+----------------+-----------+---------------------------------------+
      | product                    | Integer        | Required  | ID of Product                         |
      | category                   | Integer        | Required  | ID of Category                        |
      | priority                   | Integer        | Required  | ID of Priority                        |
      | summary                    | String         | Required  |                                       |
      | case_status                | Integer        | Optional  | ID of case status                     |
      | plan                       | Array/Str/Int  | Optional  | ID or List of plan_ids                |
      | component                  | Integer/String | Optional  | ID of Priority                        |
      | default_tester             | String         | Optional  | Login of tester                       |
      | estimated_time             | String         | Optional  | 2h30m30s(recommend) or HH:MM:SS Format|
      | is_automated               | Integer        | Optional  | 0: Manual, 1: Auto, 2: Both           |
      | is_automated_proposed      | Boolean        | Optional  | Default 0                             |
      | script                     | String         | Optional  |                                       |
      | arguments                  | String         | Optional  |                                       |
      | requirement                | String         | Optional  |                                       |
      | alias                      | String         | Optional  | Must be unique                        |
      | action                     | String         | Optional  |                                       |
      | effect                     | String         | Optional  | Expected Result                       |
      | setup                      | String         | Optional  |                                       |
      | breakdown                  | String         | Optional  |                                       |
      | tag                        | Array/String   | Optional  | String Comma separated                |
      | bug                        | Array/String   | Optional  | String Comma separated                |
      | extra_link                 | String         | Optional  | reference link                        |
      +----------------------------+----------------+-----------+---------------------------------------+

    Returns:     Array/Hash: The newly created object hash if a single case was created, or
                             an array of objects if more than one was created. If any single case threw an
                             error during creation, a hash with an ERROR key will be set in its place.

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
    from tcms.core import forms
    from tcms.xmlrpc.forms import NewCaseForm

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
        for tag in TestTag.string_to_list(values.get('tag', [])):
            t, c = TestTag.objects.get_or_create(name=tag)
            tc.add_tag(tag=t)
    else:
        # Print the errors if the form is not passed validation.
        raise ValueError(forms.errors_to_list(form))

    return get(request, tc.case_id)


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.delete_testcasebug'))
def detach_bug(request, case_ids, bug_ids):
    """
    Description: Remove one or more bugs to the selected test cases.

    Params:      $case_ids - Integer/Array/String: An integer representing the ID in the database,
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

    return


@log_call(namespace=__xmlrpc_namespace__)
def filter(request, query):
    """
    Description: Performs a search and returns the resulting list of test cases.

    Params:      $query - Hash: keys must match valid search fields.

        +------------------------------------------------------------------+
        |                 Case Search Parameters                           |
        +------------------------------------------------------------------+
        |        Key          |          Valid Values                      |
        | author              | A bugzilla login (email address)           |
        | attachment          | ForeignKey: Attchment                      |
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


@log_call(namespace=__xmlrpc_namespace__)
def filter_count(request, values={}):
    """
    Description: Performs a search and returns the resulting count of cases.

    Params:      $values - Hash: keys must match valid search fields (see filter).

    Returns:     Integer - total matching cases.

    Example:
    # See TestCase.filter()
    """

    if values.get('estimated_time'):
        values['estimated_time'] = timedelta2int(
            pre_process_estimated_time(values.get('estimated_time'))
        )

    return distinct_count(TestCase, values)


@log_call(namespace=__xmlrpc_namespace__)
def get(request, case_id):
    """
    Description: Used to load an existing test case from the database.

    Params:      $id - Integer/String: An integer representing the ID in the database

    Returns:     A blessed TestCase object Hash

    Example:
    >>> TestCase.get(1193)
    """
    try:
        tc = TestCase.objects.get(case_id=case_id)
    except:
        raise

    tc_latest_text = tc.latest_text().serialize()

    response = tc.serialize()
    response['text'] = tc_latest_text
    # get the xmlrpc tags
    tag_ids = tc.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    tags = TestTag.to_xmlrpc(query)
    # cut 'id' attribute off, only leave 'name' here
    tags_without_id = map(lambda x: x["name"], tags)
    # replace tag_id list in the serialize return data
    response["tag"] = tags_without_id
    return response


@log_call(namespace=__xmlrpc_namespace__)
def get_bug_systems(request, id):
    """
    Description: Used to load an existing test case bug system from the database.

    Params:      $id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of bug object hashes.

    Example:
    >>> TestCase.get_bug_systems(1)
    """
    from tcms.testcases.models import TestCaseBugSystem

    return TestCaseBugSystem.objects.get(pk=id).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def get_bugs(request, case_ids):
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


@log_call(namespace=__xmlrpc_namespace__)
def get_case_run_history(request, case_id):
    """
    *** FIXME: NOT IMPLEMENTED - Case run history is different than before***
    Description: Get the list of case-runs for all runs this case appears in.
                 To limit this list by build or other attribute, see TestCaseRun.filter.

    Params:      $case_id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of case-run object hashes.

    Example:
    >>> TestCase.get_case_run_history(12345)
    """
    raise NotImplementedError('Not implemented RPC method')


@log_call(namespace=__xmlrpc_namespace__)
def get_case_status(request, id=None):
    """
    Description: Get the case status matching the given id.

    Params:      $id - Integer: ID of the case status in the database.

    Returns:     Hash: case status object hash.

    Example:
    # Get all of case status
    >>> TestCase.get_case_status()
    # Get case status by ID 1
    >>> TestCase.get_case_status(1)
    """
    from tcms.testcases.models import TestCaseStatus

    if id:
        return TestCaseStatus.objects.get(id=id).serialize()

    return TestCaseStatus.to_xmlrpc()


@log_call(namespace=__xmlrpc_namespace__)
def get_change_history(request, case_id):
    """
    *** FIXME: NOT IMPLEMENTED - Case history is different than before***
    Description: Get the list of changes to the fields of this case.

    Params:      $case_id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of hashes with changed fields and their details.

    Example:
    >>> TestCase.get_change_history(12345)
    """
    raise NotImplementedError('Not implemented RPC method')


@log_call(namespace=__xmlrpc_namespace__)
def get_components(request, case_id):
    """"
    Description: Get the list of components attached to this case.

    Params:      $case_id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of component object hashes.

    Example:
    >>> TestCase.get_components(12345)
    """
    from tcms.management.models import Component

    try:
        tc = TestCase.objects.get(case_id=case_id)
    except:
        raise

    component_ids = tc.component.values_list('id', flat=True)
    query = {'id__in': component_ids}
    return Component.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_plans(request, case_id):
    """
    Description: Get the list of plans that this case is linked to.

    Params:      $case_id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of test plan object hashes.

    Example:
    >>> TestCase.get_plans(12345)
    """
    try:
        tc = TestCase.objects.get(case_id=case_id)
    except:
        raise

    plan_ids = tc.plan.values_list('plan_id', flat=True)
    query = {'plan_id__in': plan_ids}
    return TestPlan.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_tags(request, case_id):
    """
    Description: Get the list of tags attached to this case.

    Params:      $case_id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of tag object hashes.

    Example:
    >>> TestCase.get_tags(12345)
    """
    try:
        tc = TestCase.objects.get(case_id=case_id)
    except:
        raise

    tag_ids = tc.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    return TestTag.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_text(request, case_id, case_text_version=None):
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
    try:
        tc = TestCase.objects.get(case_id=case_id)
    except:
        raise

    return tc.get_text_with_version(
        case_text_version=case_text_version).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def get_priority(request, id):
    """
    Description: Get the priority matching the given id.

    Params:      $id - Integer: ID of the priority in the database.

    Returns:     Hash: Priority object hash.

    Example:
    >>> TestCase.get_priority(1)
    """
    from tcms.management.models import Priority

    return Priority.objects.get(id=id).serialize()


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.add_testcaseplan'))
def link_plan(request, case_ids, plan_ids):
    """"
    Description: Link test cases to the given plan.

    Params:      $case_ids - Integer/Array/String: An integer representing the ID in the database,
                             an array of case_ids, or a string of comma separated case_ids.

                 $plan_ids - Integer/Array/String: An integer representing the ID in the database,
                             an array of plan_ids, or a string of comma separated plan_ids.

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occurs

    Example:
    # Add case 1234 to plan id 54321
    >>> TestCase.link_plan(1234, 54321)
    # Add case ids list [56789, 12345] to plan list [1234, 5678]
    >>> TestCase.link_plan([56789, 12345], [1234, 5678])
    # Add case ids list 56789 and 12345 to plan list 1234 and 5678 with String
    >>> TestCase.link_plan('56789, 12345', '1234, 5678')
    """
    case_ids = pre_process_ids(value=case_ids)
    qs = TestCase.objects.filter(pk__in=case_ids)
    tcs_ids = qs.values_list('pk', flat=True)

    # Check the non-exist case ids.
    ids_diff = set(case_ids) - set(tcs_ids.iterator())
    if ids_diff:
        ids_str = ','.join(imap(str, ids_diff))
        if len(ids_diff) > 1:
            err_msg = 'TestCases %s do not exist.' % ids_str
        else:
            err_msg = 'TestCase %s does not exist.' % ids_str
        raise ObjectDoesNotExist(err_msg)

    plan_ids = pre_process_ids(value=plan_ids)
    qs = TestPlan.objects.filter(pk__in=plan_ids)
    tps_ids = qs.values_list('pk', flat=True)

    # Check the non-exist plan ids.
    ids_diff = set(plan_ids) - set(tps_ids.iterator())
    if ids_diff:
        ids_str = ','.join(imap(str, ids_diff))
        if len(ids_diff) > 1:
            err_msg = 'TestPlans %s do not exist.' % ids_str
        else:
            err_msg = 'TestPlan %s does not exist.' % ids_str
        raise ObjectDoesNotExist(err_msg)

    # (plan_id, case_id) pair might probably exist in test_case_plans table, so
    # skip the ones that do exist and create the rest.
    # note: this query returns a list of tuples!
    existing = TestCasePlan.objects.filter(
        plan__in=plan_ids,
        case__in=case_ids
    ).values_list('plan', 'case')

    # Link the plans to cases
    def _generate_link_plan_value():
        for plan_id in plan_ids:
            for case_id in case_ids:
                if (plan_id, case_id) not in existing:
                    yield plan_id, case_id

    TestCasePlan.objects.bulk_create([
        TestCasePlan(plan_id=_plan_id, case_id=_case_id)
        for _plan_id, _case_id in _generate_link_plan_value()
    ])


@log_call(namespace=__xmlrpc_namespace__)
def lookup_category_name_by_id(request, id):
    """DEPRECATED - CONSIDERED HARMFUL Use Product.get_category instead"""
    from product import get_category

    return get_category(request=request, id=id)


@log_call(namespace=__xmlrpc_namespace__)
def lookup_category_id_by_name(request, name, product):
    """
    DEPRECATED - CONSIDERED HARMFUL Use Product.check_category instead
    """
    from product import check_category

    return check_category(request=request, name=name, product=product)


@log_call(namespace=__xmlrpc_namespace__)
def lookup_priority_name_by_id(request, id):
    """
    DEPRECATED - CONSIDERED HARMFUL Use TestCase.get_priority instead
    """
    return get_priority(request=request, id=id)


@log_call(namespace=__xmlrpc_namespace__)
def lookup_priority_id_by_name(request, value):
    """
    DEPRECATED - CONSIDERED HARMFUL Use TestCase.check_priority instead
    """
    return check_priority(request=request, value=value)


@log_call(namespace=__xmlrpc_namespace__)
def lookup_status_name_by_id(request, id):
    """DEPRECATED - CONSIDERED HARMFUL Use TestCase.get_case_status instead"""
    return get_case_status(request=request, id=id)


@log_call(namespace=__xmlrpc_namespace__)
def lookup_status_id_by_name(request, name):
    """DEPRECATED - CONSIDERED HARMFUL Use TestCase.check_case_status instead"""
    return check_case_status(request=request, name=name)


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.delete_testcasecomponent'))
def remove_component(request, case_ids, component_ids):
    """
    Description: Removes selected component from the selected test case.

    Params:      $case_ids - Integer/Array/String: An integer representing the ID in the database,
                             an array of case_ids, or a string of comma separated case_ids.

                 $component_ids - Integer: - The component ID to be removed.

    Returns:     Array: Empty on success.

    Example:
    # Remove component id 54321 from case 1234
    >>> TestCase.remove_component(1234, 54321)
    # Remove component ids list [1234, 5678] from cases list [56789, 12345]
    >>> TestCase.remove_component([56789, 12345], [1234, 5678])
    # Remove component ids list '1234, 5678' from cases list '56789, 12345' with String
    >>> TestCase.remove_component('56789, 12345', '1234, 5678')
    """
    from tcms.management.models import Component

    tcs = TestCase.objects.filter(
        case_id__in=pre_process_ids(value=case_ids)
    )
    tccs = Component.objects.filter(
        id__in=pre_process_ids(value=component_ids)
    )

    for tc in tcs.iterator():
        for tcc in tccs.iterator():
            try:
                tc.remove_component(component=tcc)
            except ObjectDoesNotExist:
                pass

    return


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.delete_testcasetag'))
def remove_tag(request, case_ids, tags):
    """
    Description: Remove a tag from a case.

    Params:      $case_ids - Integer/Array/String: An integer or alias representing the ID in the database,
                             an array of case_ids, or a string of comma separated case_ids.

                 $tags - String/Array - A single or multiple tag to be removed.

    Returns:     Array: Empty on success.

    Example:
    # Remove tag 'foo' from case 1234
    >>> TestCase.remove_tag(1234, 'foo')
    # Remove tag 'foo' and bar from cases list [56789, 12345]
    >>> TestCase.remove_tag([56789, 12345], ['foo', 'bar'])
    # Remove tag 'foo' and 'bar' from cases list '56789, 12345' with String
    >>> TestCase.remove_tag('56789, 12345', 'foo, bar')
    """
    tcs = TestCase.objects.filter(
        case_id__in=pre_process_ids(value=case_ids)
    )
    tgs = TestTag.objects.filter(
        name__in=TestTag.string_to_list(tags)
    )

    for tc in tcs.iterator():
        for tg in tgs.iterator():
            try:
                tc.remove_tag(tg)
            except ObjectDoesNotExist:
                pass
            except:
                raise

    return


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.add_testcasetext'))
def store_text(request, case_id, action, effect='', setup='', breakdown='',
               author_id=None):
    """
    Description: Update the large text fields of a case.

    Params:      $case_id - Integer: An integer or alias representing the ID in the database.
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

    try:
        tc = TestCase.objects.get(case_id=case_id)
    except:
        raise

    if author_id:
        author = User.objects.get(id=author_id)
    else:
        author = request.user

    return tc.add_text(
        author=author,
        action=action and action.strip(),
        effect=effect and effect.strip(),
        setup=setup and setup.strip(),
        breakdown=breakdown and breakdown.strip(),
    ).serialize()


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.delete_testcaseplan'))
def unlink_plan(requst, case_id, plan_id):
    """
    Description: Unlink a test case from the given plan. If only one plan is linked, this will delete
                 the test case.

    Params:      $case_id - Integer/String: An integer or alias representing the ID in the database.
                 $plan_id - Integer: An integer representing the ID in the database.

    Returns:     Array: Array of plans hash still linked if any, empty if not.

    Example:
    >>> TestCase.unlink_plan(12345, 137)
    """
    TestCasePlan.objects.filter(case=case_id, plan=plan_id).delete()
    plan_pks = TestCasePlan.objects.filter(case=case_id).values_list('plan',
                                                                     flat=True)
    return TestPlan.to_xmlrpc(query={'pk__in': plan_pks})


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.change_testcase'))
def update(request, case_ids, values):
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
    from tcms.core import forms
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
        raise ValueError(forms.errors_to_list(form))

    query = {'pk__in': tcs.values_list('pk', flat=True)}
    return TestCase.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def validate_cc_list(cc_list):
    '''Validate each email in cc_list argument

    This is called by ``notification_*`` methods internally.

    No return value, and if any email in cc_list is not valid, ValidationError
    will be raised.
    '''

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


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.change_testcase'))
def notification_add_cc(request, case_ids, cc_list):
    '''
    Description: Add email addresses to the notification CC list of specific TestCases

    Params:      $case_ids - Integer/Array: one or more TestCase IDs

                 $cc_list - Array: one or more Email addresses, which will be
                            added to each TestCase indicated by the case_ids.

    Returns:     JSON. When succeed, status is 0, and message maybe empty or
                 anything else that depends on the implementation. If something
                 wrong, status will be 1 and message will be a short description
                 to the error.
    '''

    try:
        validate_cc_list(cc_list)
    except (TypeError, ValidationError):
        raise

    try:
        tc_ids = pre_process_ids(case_ids)

        for tc in TestCase.objects.filter(pk__in=tc_ids).iterator():
            # First, find those that do not exist yet.
            existing_cc = tc.emailing.get_cc_list()
            adding_cc = list(set(cc_list) - set(existing_cc))

            tc.emailing.add_cc(adding_cc)

    except (TypeError, ValueError, Exception):
        raise


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.change_testcase'))
def notification_remove_cc(request, case_ids, cc_list):
    '''
    Description: Remove email addresses from the notification CC list of specific TestCases

    Params:      $case_ids - Integer/Array: one or more TestCase IDs

                 $cc_list - Array: contians the email addresses that will
                            be removed from each TestCase indicated by case_ids.

    Returns:     JSON. When succeed, status is 0, and message maybe empty or
                 anything else that depends on the implementation. If something
                 wrong, status will be 1 and message will be a short description
                 to the error.
    '''

    try:
        validate_cc_list(cc_list)
    except (TypeError, ValidationError):
        raise

    try:
        tc_ids = pre_process_ids(case_ids)

        for tc in TestCase.objects.filter(pk__in=tc_ids).only('pk').iterator():
            tc.emailing.remove_cc(cc_list)

    except (TypeError, ValueError, Exception):
        raise


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('testcases.change_testcase'))
def notification_get_cc_list(request, case_ids):
    '''
    Description: Return whole CC list of each TestCase

    Params:      $case_ids - Integer/Array: one or more TestCase IDs

    Returns:     An dictionary object with case_id as key and a list of CC as the value
                 Each case_id will be converted to a str object in the result.
    '''

    result = {}

    try:
        tc_ids = pre_process_ids(case_ids)

        for tc in TestCase.objects.filter(pk__in=tc_ids).iterator():
            cc_list = tc.emailing.get_cc_list()
            result[str(tc.pk)] = cc_list

    except (TypeError, ValueError, Exception):
        raise

    return result
