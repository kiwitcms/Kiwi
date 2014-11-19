# -*- coding: utf-8 -*-

from kobo.django.xmlrpc.decorators import user_passes_test

from tcms.xmlrpc.decorators import log_call
from tcms.management.models import TestBuild
from tcms.xmlrpc.utils import pre_check_product, parse_bool_value

__all__ = (
    'check_build', 'create', 'get', 'get_runs', 'get_caseruns',
    'lookup_id_by_name', 'lookup_name_by_id', 'update'
)

__xmlrpc_namespace__ = 'TestBuild'


@log_call(namespace=__xmlrpc_namespace__)
def check_build(request, name, product):
    """
    Description: Looks up and returns a build by name.

    Params:      $name - String: name of the build.
                 $product - product_id of the product in the Database

    Returns:     Hash: Matching Build object hash or error if not found.

    Example:
    # Get with product ID
    >>> Build.check_build('2008-02-25', 61)
    # Get with product name
    >>> Build.check_build('2008-02-25', 'Red Hat Enterprise Linux 5')
    """
    p = pre_check_product(values=product)
    tb = TestBuild.objects.get(name=name, product=p)
    return tb.serialize()


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('management.add_testbuild'))
def create(request, values):
    """
    Description: Creates a new build object and stores it in the database

    Params:      $values - Hash: A reference to a hash with keys and values
                 matching the fields of the build to be created.

        +-------------+----------------+-----------+---------------------------+
        | Field       | Type           | Null      | Description               |
        +-------------+----------------+-----------+---------------------------+
        | product     | Integer/String | Required  | ID or Name of product     |
        | name        | String         | Required  |                           |
        | description | String         | Optional  |                           |
        | is_active   | Boolean        | Optional  | Defaults to True (1)      |
        +-------------+----------------+-----------+---------------------------+

    Returns:     The newly created object hash.

    Example:
    # Create build by product ID and set the build active.
    >>> Build.create({'product': 234, 'name': 'tcms_testing', 'description': 'None', 'is_active': 1})
    # Create build by product name and set the build to inactive.
    >>> Build.create({'product': 'TCMS', 'name': 'tcms_testing 2', 'description': 'None', 'is_active': 0})
    """
    if not values.get('product') or not values.get('name'):
        raise ValueError('Product and name are both required.')

    p = pre_check_product(values)

    return TestBuild.objects.create(
        product=p,
        name=values['name'],
        description=values.get('description'),
        is_active=parse_bool_value(values.get('is_active', True))
    ).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def get(request, build_id):
    """
    Description: Used to load an existing build from the database.

    Params:      $id - An integer representing the ID in the database

    Returns:     A blessed Build object hash

    Example:
    >>> Build.get(1234)
    """
    return TestBuild.objects.get(build_id=build_id).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def get_runs(request, build_id):
    """
    Description: Returns the list of runs that this Build is used in.

    Params:      $id -  Integer: Build ID.

    Returns:     Array: List of run object hashes.

    Example:
    >>> Build.get_runs(1234)
    """
    from tcms.testruns.models import TestRun

    tb = TestBuild.objects.get(build_id=build_id)
    query = {'build': tb}

    return TestRun.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_caseruns(request, build_id):
    """
    Description: Returns the list of case-runs that this Build is used in.

    Params:      $id -  Integer: Build ID.

    Returns:     Array: List of case-run object hashes.

    Example:
    >>> Build.get_caseruns(1234)
    """
    from tcms.testruns.models import TestCaseRun

    tb = TestBuild.objects.get(build_id=build_id)
    query = {'build': tb}

    return TestCaseRun.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def lookup_id_by_name(request, name, product):
    """
    DEPRECATED - CONSIDERED HARMFUL Use Build.check_build instead
    """
    return check_build(request, name, product)


@log_call(namespace=__xmlrpc_namespace__)
def lookup_name_by_id(request, build_id):
    """
    DEPRECATED Use Build.get instead
    """
    return get(request, build_id)


@log_call(namespace=__xmlrpc_namespace__)
@user_passes_test(lambda u: u.has_perm('management.change_testbuild'))
def update(request, build_id, values):
    """
    Description: Updates the fields of the selected build or builds.

    Params:      $id - Integer: A single build ID.

                 $values - Hash of keys matching Build fields and the new values
                 to set each field to.

        +-------------+----------------+-----------+---------------------------+
        | Field       | Type           | Null      | Description               |
        +-------------+----------------+-----------+---------------------------+
        | product     | Integer/String | Optional  | ID or Name of product     |
        | name        | String         | Optional  |                           |
        | description | String         | Optional  |                           |
        | is_active   | Boolean        | Optional  | True/False                |
        +-------------+----------------+-----------+---------------------------+

    Returns:     Hash: The updated Build object hash.

    Example:
    # Update name to 'foo' for build id 702
    >>> Build.update(702, {'name': 'foo'})
    # Update status to inactive for build id 702
    >>> Build.update(702, {'is_active': 0})
    """
    tb = TestBuild.objects.get(build_id=build_id)

    def _update_value(obj, name, value):
        setattr(obj, name, value)
        update_fields.append(name)

    update_fields = list()
    if values.get('product'):
        _update_value(tb, 'product', pre_check_product(values))
    if values.get('name'):
        _update_value(tb, 'name', values['name'])
    if values.get('description'):
        _update_value(tb, 'description', values['description'])
    if values.get('is_active') is not None:
        _update_value(tb, 'is_active', parse_bool_value(values.get(
            'is_active', True)))

    tb.save(update_fields=update_fields)

    return tb.serialize()
