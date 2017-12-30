# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method, REQUEST_KEY

from tcms.management.models import Component
from tcms.management.models import TestTag
from tcms.management.models import Product
from tcms.testplans.models import TestPlan, TestPlanType, TCMSEnvPlanMap
from tcms.xmlrpc.decorators import permissions_required
from tcms.xmlrpc.utils import pre_process_ids, distinct_count

__all__ = (
    'add_tag',
    'add_component',
    'check_plan_type',
    'create',
    'filter',
    'filter_count',
    'get',
    'get_env_groups',
    'get_plan_type',
    'get_product',
    'get_tags',
    'get_components',
    'get_test_cases',
    'get_all_cases_tags',
    'get_test_runs',
    'get_text',
    'remove_tag',
    'remove_component',
    'store_text',
    'update',
)


@permissions_required('testplans.add_testplantag')
@rpc_method(name='TestPlan.add_tag')
def add_tag(plan_ids, tags):
    """
    Description: Add one or more tags to the selected test plans.

    Params:      $plan_ids - Integer/Array/String: An integer representing the ID of the plan
                      in the database,
                      an arry of plan_ids, or a string of comma separated plan_ids.

                  $tags - String/Array - A single tag, an array of tags,
                      or a comma separated list of tags.

    Returns:     Array: empty on success or an array of hashes with failure
                  codes if a failure occured.

    Example:
    # Add tag 'foobar' to plan 1234
    >>> TestPlan.add_tag(1234, 'foobar')
    # Add tag list ['foo', 'bar'] to plan list [12345, 67890]
    >>> TestPlan.add_tag([12345, 67890], ['foo', 'bar'])
    # Add tag list ['foo', 'bar'] to plan list [12345, 67890] with String
    >>> TestPlan.add_tag('12345, 67890', 'foo, bar')
    """
    # FIXME: this could be optimized to reduce possible huge number of SQLs

    tps = TestPlan.objects.filter(plan_id__in=pre_process_ids(value=plan_ids))

    if not isinstance(tags, (str, list)):
        raise ValueError('Parameter tags must be a string or list(string)')

    tags = TestTag.string_to_list(tags)

    for tag in tags:
        t, c = TestTag.objects.get_or_create(name=tag)
        for tp in tps.iterator():
            tp.add_tag(tag=t)

    return


@permissions_required('testplans.add_testplancomponent')
@rpc_method(name='TestPlan.add_component')
def add_component(plan_ids, component_ids):
    """
    Description: Adds one or more components to the selected test plan.

    Params:      $plan_ids - Integer/Array/String: An integer representing the ID of the plan
                             in the database.
                 $component_ids - Integer/Array/String - The component ID, an array of
                                  Component IDs or a comma separated list of component IDs.

    Returns:     Array: empty on success or an array of hashes with failure
                        codes if a failure occured.

    Example:
    # Add component id 54321 to plan 1234
    >>> TestPlan.add_component(1234, 54321)
    # Add component ids list [1234, 5678] to plan list [56789, 12345]
    >>> TestPlan.add_component([56789, 12345], [1234, 5678])
    # Add component ids list '1234, 5678' to plan list '56789, 12345' with String
    >>> TestPlan.add_component('56789, 12345', '1234, 5678')
    """
    # FIXME: optimize this method to reduce possible huge number of SQLs

    tps = TestPlan.objects.filter(
        plan_id__in=pre_process_ids(value=plan_ids)
    )
    cs = Component.objects.filter(
        id__in=pre_process_ids(value=component_ids)
    )

    for tp in tps.iterator():
        for c in cs.iterator():
            tp.add_component(c)

    return


@rpc_method(name='TestPlan.check_plan_type')
def check_plan_type(name):
    """
    Params:      $name - String: the plan type.

    Returns:     Hash: Matching plan type object hash or error if not found.

    Example:
    >>> TestPlan.check_plan_type('regression')
    """
    return TestPlanType.objects.get(name=name).serialize()


@permissions_required('testplans.add_testplan')
@rpc_method(name='TestPlan.create')
def create(values, **kwargs):
    """
    Description: Creates a new Test Plan object and stores it in the database.

    Params:      $values - Hash: A reference to a hash with keys and values
                  matching the fields of the test plan to be created.
     +--------------------------+---------+-----------+-------------------------------------------+
     | Field                    | Type    | Null      | Description                               |
     +--------------------------+---------+-----------+-------------------------------------------+
     | product                  | Integer | Required  | ID of product                             |
     | name                     | String  | Required  |                                           |
     | type                     | Integer | Required  | ID of plan type                           |
     | product_version          | Integer | Required  | ID of version, product_version(recommend),|
     | (default_product_version)|         |           | default_product_version will be deprecated|
     |                          |         |           | in future release.                        |
     | text                     | String  | Required  | Plan documents, HTML acceptable.          |
     | parent                   | Integer | Optional  | Parent plan ID                            |
     | is_active                | Boolean | Optional  | 0: Archived 1: Active (Default 0)         |
     +--------------------------+---------+-----------+-------------------------------------------+

    Returns:     The newly created object hash.

    Example:
    # Minimal test case parameters
    >>> values = {
        'product': 61,
        'name': 'Testplan foobar',
        'type': 1,
        'parent_id': 150,
        'default_product_version': 93,
        'text':'Testing TCMS',
    }
    >>> TestPlan.create(values)
    """
    from tcms.core import forms
    from tcms.xmlrpc.forms import NewPlanForm

    if values.get('default_product_version'):
        values['product_version'] = values.pop('default_product_version')

    if not values.get('product'):
        raise ValueError('Value of product is required')

    form = NewPlanForm(values)
    form.populate(product_id=values['product'])

    if form.is_valid():
        request = kwargs.get(REQUEST_KEY)
        tp = TestPlan.objects.create(
            product=form.cleaned_data['product'],
            name=form.cleaned_data['name'],
            type=form.cleaned_data['type'],
            author=request.user,
            product_version=form.cleaned_data['product_version'],
            parent=form.cleaned_data['parent'],
            is_active=form.cleaned_data['is_active']
        )

        tp.add_text(
            author=request.user,
            plan_text=values['text'],
        )

        return tp.serialize()
    else:
        raise ValueError(forms.errors_to_list(form))


@rpc_method(name='TestPlan.filter')
def filter(values={}):
    """
    Description: Performs a search and returns the resulting list of test plans.

    Params:      $values - Hash: keys must match valid search fields.

        +------------------------------------------------------------+
        |                   Plan Search Parameters                   |
        +----------------------------------------------------------+
        |        Key              |          Valid Values            |
        | author                  | ForeignKey: Auth.User            |
        | case                    | ForeignKey: Test Case            |
        | create_date             | DateTime                         |
        | env_group               | ForeignKey: Environment Group    |
        | name                    | String                           |
        | plan_id                 | Integer                          |
        | product                 | ForeignKey: Product              |
        | product_version         | ForeignKey: Version              |
        | tag                     | ForeignKey: Tag                  |
        | text                    | ForeignKey: Test Plan Text       |
        | type                    | ForeignKey: Test Plan Type       |
        +------------------------------------------------------------+

    Returns:     Array: Matching test plans are retuned in a list of plan object hashes.

    Example:
    # Get all of plans contain 'TCMS' in name
    >>> TestPlan.filter({'name__icontain': 'TCMS'})
    # Get all of plans create by xkuang
    >>> TestPlan.filter({'author__username': 'xkuang'})
    # Get all of plans the author name starts with x
    >>> TestPlan.filter({'author__username__startswith': 'x'})
    # Get plans contain the case ID 12345, 23456, 34567
    >>> TestPlan.filter({'case__case_id__in': [12345, 23456, 34567]})
    """
    return TestPlan.to_xmlrpc(values)


@rpc_method(name='TestPlan.filter_count')
def filter_count(values={}):
    """
    Description: Performs a search and returns the resulting count of plans.

    Params:      $values - Hash: keys must match valid search fields (see filter).

    Returns:     Integer - total matching plans.

    Example:
    # See distinct_count()
    """
    return distinct_count(TestPlan, values)


@rpc_method(name='TestPlan.get')
def get(plan_id):
    """
    Description: Used to load an existing test plan from the database.

    Params:      $id - Integer/String: An integer representing the ID of this plan in the database

    Returns:     Hash: A blessed TestPlan object hash

    Example:
    >>> TestPlan.get(137)
    """
    tp = TestPlan.objects.get(plan_id=plan_id)
    response = tp.serialize()

    # This is for backward-compatibility. Actually, this is not a good way to
    # add this extra field. But, now that's it.
    response['default_product_version'] = response['product_version']

    # get the xmlrpc tags
    tag_ids = tp.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    tags = TestTag.to_xmlrpc(query)
    # cut 'id' attribute off, only leave 'name' here
    tags_without_id = [x["name"] for x in tags]
    # replace tag_id list in the serialize return data
    response["tag"] = tags_without_id
    return response


@rpc_method(name='TestPlan.get_env_groups')
def get_env_groups(plan_id):
    """
    Description: Get the list of env groups to the fields of this plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database

    Returns:     Array: An array of hashes with env groups.
    """
    from tcms.management.models import TCMSEnvGroup

    query = {'testplan__pk': plan_id}
    return TCMSEnvGroup.to_xmlrpc(query)


@rpc_method(name='TestPlan.get_plan_type')
def get_plan_type(id):
    """
    Params:      $id - Integer: ID of the plan type to return

    Returns:     Hash: Matching plan type object hash or error if not found.

    Example:
    >>> TestPlan.get_plan_type(3)
    """
    return TestPlanType.objects.get(id=id).serialize()


@rpc_method(name='TestPlan.get_product')
def get_product(plan_id):
    """
    Description: Get the Product the plan is assiciated with.

    Params:      $plan_id - Integer: An integer representing the ID of the plan in the database.

    Returns:     Hash: A blessed Product hash.

    Example:
    >>> TestPlan.get_product(137)
    """
    products = Product.objects.filter(plan=plan_id)
    products = products.select_related('classification')
    products = products.defer('classification__description')
    if len(products) == 0:
        raise Product.DoesNotExist('Product matching query does not exist')
    else:
        return products[0].serialize()


@rpc_method(name='TestPlan.get_tags')
def get_tags(plan_id):
    """
    Description: Get the list of tags attached to this plan.

    Params:      $plan_id - Integer An integer representing the ID of this plan in the database

    Returns:     Array: An array of tag object hashes.

    Example:
    >>> TestPlan.get_tags(137)
    """
    test_plan = TestPlan.objects.get(plan_id=plan_id)

    tag_ids = test_plan.tag.values_list('id', flat=True)
    query = {'id__in': tag_ids}
    return TestTag.to_xmlrpc(query)


@rpc_method(name='TestPlan.get_components')
def get_components(plan_id):
    """
    Description: Get the list of components attached to this plan.

    Params:      $plan_id - Integer/String: An integer representing the ID in the database

    Returns:     Array: An array of component object hashes.

    Example:
    >>> TestPlan.get_components(12345)
    """
    test_plan = TestPlan.objects.get(plan_id=plan_id)

    component_ids = test_plan.component.values_list('id', flat=True)
    query = {'id__in': component_ids}
    return Component.to_xmlrpc(query)


@rpc_method(name='TestPlan.get_all_cases_tags')
def get_all_cases_tags(plan_id):
    """
    Description: Get the list of tags attached to this plan's testcases.

    Params:      $plan_id - Integer An integer representing the ID of this plan in the database

    Returns:     Array: An array of tag object hashes.

    Example:
    >>> TestPlan.get_all_cases_tags(137)
    """
    test_plan = TestPlan.objects.get(plan_id=plan_id)

    test_cases = test_plan.case.all()
    tag_ids = []
    for test_case in test_cases.iterator():
        tag_ids.extend(test_case.tag.values_list('id', flat=True))
    tag_ids = list(set(tag_ids))
    query = {'id__in': tag_ids}
    return TestTag.to_xmlrpc(query)


@rpc_method(name='TestPlan.get_test_cases')
def get_test_cases(plan_id):
    """
    Description: Get the list of cases that this plan is linked to.

    Params:      $plan_id - Integer: An integer representing the ID of the plan in the database

    Returns:     Array: An array of test case object hashes.

    Example:
    >>> TestPlan.get_test_cases(137)
    """
    from tcms.testcases.models import TestCase
    from tcms.testplans.models import TestPlan
    from tcms.xmlrpc.serializer import XMLRPCSerializer

    tp = TestPlan.objects.get(pk=plan_id)
    tcs = TestCase.objects.filter(plan=tp).order_by('testcaseplan__sortkey')
    serialized_tcs = XMLRPCSerializer(tcs.iterator()).serialize_queryset()
    if serialized_tcs:
        for serialized_tc in serialized_tcs:
            case_id = serialized_tc.get('case_id', None)
            tc = tcs.get(pk=case_id)
            tcp = tc.testcaseplan_set.get(plan=tp)
            serialized_tc['sortkey'] = tcp.sortkey
    return serialized_tcs


@rpc_method(name='TestPlan.get_test_runs')
def get_test_runs(plan_id):
    """
    Description: Get the list of runs in this plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database

    Returns:     Array: An array of test run object hashes.

    Example:
    >>> TestPlan.get_test_runs(plan_id)
    """
    from tcms.testruns.models import TestRun

    query = {'plan': plan_id}
    return TestRun.to_xmlrpc(query)


@rpc_method(name='TestPlan.get_text')
def get_text(plan_id, plan_text_version=None):
    """
    Description: The plan document for a given test plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database

                 $version - Integer: (OPTIONAL) The version of the text you want returned.
                                     Defaults to the latest.

    Returns:     Hash: Text and author information.

    Example:
    # Get all latest case text
    >>> TestPlan.get_text(137)
    # Get all case text with version 4
    >>> TestPlan.get_text(137, 4)
    """
    tp = TestPlan.objects.get(plan_id=plan_id)
    test_plan_text = tp.get_text_with_version(
        plan_text_version=plan_text_version)
    if test_plan_text:
        return test_plan_text.serialize()
    else:
        return "No plan text with version '%s' found." % plan_text_version


@permissions_required('testplans.delete_testplantag')
@rpc_method(name='TestPlan.remove_tag')
def remove_tag(plan_ids, tags):
    """
    Description: Remove a tag from a plan.

    Params:      $plan_ids - Integer/Array/String: An integer or alias representing the ID
                                                   in the database, an array of plan_ids,
                                                   or a string of comma separated plan_ids.

                 $tag - String - A single tag to be removed.

    Returns:     Array: Empty on success.

    Example:
    # Remove tag 'foo' from plan 1234
    >>> TestPlan.remove_tag(1234, 'foo')
    # Remove tag 'foo' and 'bar' from plan list [56789, 12345]
    >>> TestPlan.remove_tag([56789, 12345], ['foo', 'bar'])
    # Remove tag 'foo' and 'bar' from plan list '56789, 12345' with String
    >>> TestPlan.remove_tag('56789, 12345', 'foo, bar')
    """
    from tcms.management.models import TestTag

    test_plans = TestPlan.objects.filter(
        plan_id__in=pre_process_ids(value=plan_ids)
    )

    if not isinstance(tags, (str, list)):
        raise ValueError('Parameter tags must be a string or list(string)')

    test_tags = TestTag.objects.filter(
        name__in=TestTag.string_to_list(tags)
    )

    for test_plan in test_plans.iterator():
        for test_tag in test_tags.iterator():
            test_plan.remove_tag(tag=test_tag)

    return


@permissions_required('testplans.delete_testplancomponent')
@rpc_method(name='TestPlan.remove_component')
def remove_component(plan_ids, component_ids):
    """
    Description: Removes selected component from the selected test plan.

    Params:      $plan_ids - Integer/Array/String: An integer representing the ID in the database,
                             an array of plan_ids, or a string of comma separated plan_ids.

                 $component_ids - Integer: - The component ID to be removed.

    Returns:     Array: Empty on success.

    Example:
    # Remove component id 54321 from plan 1234
    >>> TestPlan.remove_component(1234, 54321)
    # Remove component ids list [1234, 5678] from plan list [56789, 12345]
    >>> TestPlan.remove_component([56789, 12345], [1234, 5678])
    # Remove component ids list '1234, 5678' from plan list '56789, 12345' with String
    >>> TestPlan.remove_component('56789, 12345', '1234, 5678')
    """
    test_plans = TestPlan.objects.filter(
        plan_id__in=pre_process_ids(value=plan_ids)
    )
    components = Component.objects.filter(
        id__in=pre_process_ids(value=component_ids)
    )

    for test_plan in test_plans.iterator():
        for component in components.iterator():
            test_plan.remove_component(component=component)

    return


@permissions_required('testplans.add_testplantext')
@rpc_method(name='TestPlan.store_text')
def store_text(plan_id, text, **kwargs):
    """
    Description: Update the document field of a plan.

    Params:      $plan_id - Integer: An integer representing the ID of this plan in the database.
                 $text - String: Text for the document. Can contain HTML.
                 [$author] = Integer: (OPTIONAL) The numeric ID or the login of the author.
                      Defaults to logged in user.

    Returns:     Hash: The new text object hash.

    Example:
    >>> TestPlan.store_text(1234, 'Plan Text', 2207)
    """
    from django.contrib.auth.models import User

    tp = TestPlan.objects.get(plan_id=plan_id)

    author = kwargs.get('author', None)
    if author:
        author = User.objects.get(id=author)
    else:
        request = kwargs.get(REQUEST_KEY)
        author = request.user

    return tp.add_text(
        author=author,
        plan_text=text and text.strip(),
    ).serialize()


@permissions_required('testplans.change_testplan')
@rpc_method(name='TestPlan.update')
def update(plan_ids, values):
    """
    Description: Updates the fields of the selected test plan.

    Params:      $plan_ids - Integer: A single (or list of) TestPlan ID.

                 $values - Hash of keys matching TestPlan fields and the new values
                           to set each field to.
      +---------------------------+----------------+--------------------------------------------+
      | Field                     | Type           | Description                                |
      +---------------------------+----------------+--------------------------------------------+
      | product                   | Integer        | ID of product                              |
      | name                      | String         |                                            |
      | type                      | Integer        | ID of plan type                            |
      | product_version           | Integer        | ID of version, product_version(recommend), |
      |  (default_product_version)|                | default_product_version will be deprecated |
      |                           |                | in future release.                         |
      | owner                     | String/Integer | user_name/user_id                          |
      | parent                    | Integer        | Parent plan ID                             |
      | is_active                 | Boolean        | True/False                                 |
      | env_group                 | Integer        | New environment group ID                   |
      +---------------------------+-------------------------------------------------------------+

    Returns:     Hash: The updated test plan object.

    Example:
    # Update product to 61 for plan 207 and 208
    >>> TestPlan.update([207, 208], {'product': 61})
    """
    from tcms.core import forms
    from tcms.xmlrpc.forms import EditPlanForm

    if values.get('default_product_version'):
        values['product_version'] = values.pop('default_product_version')

    form = EditPlanForm(values)

    if values.get('product_version') and not values.get('product'):
        raise ValueError('Field "product" is required by product_version')

    if values.get('product') and not values.get('product_version'):
        raise ValueError('Field "product_version" is required by product')

    if values.get('product_version') and values.get('product'):
        form.populate(product_id=values['product'])

    plan_ids = pre_process_ids(value=plan_ids)
    tps = TestPlan.objects.filter(pk__in=plan_ids)

    if form.is_valid():
        _values = dict()
        if form.cleaned_data['name']:
            _values['name'] = form.cleaned_data['name']

        if form.cleaned_data['type']:
            _values['type'] = form.cleaned_data['type']

        if form.cleaned_data['product']:
            _values['product'] = form.cleaned_data['product']

        if form.cleaned_data['product_version']:
            _values['product_version'] = form.cleaned_data[
                'product_version']

        if form.cleaned_data['owner']:
            _values['owner'] = form.cleaned_data['owner']

        if form.cleaned_data['parent']:
            _values['parent'] = form.cleaned_data['parent']

        if not (values.get('is_active') is None):
            _values['is_active'] = form.cleaned_data['is_active']

        tps.update(**_values)

        # requested to update environment group for selected test plans
        if form.cleaned_data['env_group']:
            # prepare the list of new objects to be inserted into DB
            new_objects = [
                TCMSEnvPlanMap(
                    plan_id=plan_pk,
                    group_id=form.cleaned_data['env_group'].pk
                ) for plan_pk in plan_ids
            ]

            # first delete the old values (b/c many-to-many I presume ?)
            TCMSEnvPlanMap.objects.filter(plan__in=plan_ids).delete()
            # then create all objects with 1 INSERT
            TCMSEnvPlanMap.objects.bulk_create(new_objects)
    else:
        raise ValueError(forms.errors_to_list(form))

    query = {'pk__in': tps.values_list('pk', flat=True)}
    return TestPlan.to_xmlrpc(query)
