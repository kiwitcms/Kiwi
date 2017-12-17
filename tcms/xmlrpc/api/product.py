# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User

from tcms.management.models import Product
from tcms.xmlrpc.decorators import log_call
from tcms.xmlrpc.utils import pre_check_product, parse_bool_value

__all__ = (
    'check_category',
    'check_component',
    'check_product',
    'filter',
    'filter_categories',
    'filter_components',
    'filter_versions',
    'get',
    'get_builds',
    'get_cases',
    'get_categories',
    'get_category',
    'add_component',
    'get_component',
    'update_component',
    'get_components',
    'get_environments',
    'get_milestones',
    'get_plans',
    'get_runs',
    'get_tag',
    'add_version',
    'get_versions',
)

__xmlrpc_namespace__ = 'Product'


@log_call(namespace=__xmlrpc_namespace__)
def check_category(request, name, product):
    """
    Description: Looks up and returns a category by name.

    Params:      $name - String: name of the category.
                 $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Hash: Matching Category object hash or error if not found.

    Example:
    # Get with product ID
    >>> Product.check_category('Feature', 61)
    # Get with product name
    >>> Product.check_category('Feature', 'Red Hat Enterprise Linux 5')
    """
    from tcms.testcases.models import TestCaseCategory

    p = pre_check_product(values=product)
    return TestCaseCategory.objects.get(name=name, product=p).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def check_component(request, name, product):
    """
    Description: Looks up and returns a component by name.

    Params:      $name - String: name of the category.
                 $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Hash: Matching component object hash or error if not found.

    Example:
    # Get with product ID
    >>> Product.check_component('acpi', 61)
    # Get with product name
    >>> Product.check_component('acpi', 'Red Hat Enterprise Linux 5')
    """
    from tcms.management.models import Component

    p = pre_check_product(values=product)
    return Component.objects.get(name=name, product=p).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def check_product(request, name):
    """
    Description: Looks up and returns a validated product.

    Params:      $name - Integer/String
                         Integer: product_id of the product in the Database
                         String: Product name

    Returns:     Hash: Matching Product object hash or error if not found.

    Example:
    # Get with product ID
    >>> Product.check_product(61)
    # Get with product name
    >>> Product.check_product('Red Hat Enterprise Linux 5')
    """
    p = pre_check_product(values=name)
    return p.serialize()


@log_call(namespace=__xmlrpc_namespace__)
def filter(request, query):
    """
    Description: Performs a search and returns the resulting list of products.

    Params:      $query - Hash: keys must match valid search fields.

    +------------------------------------------------------------------+
    |               Product Search Parameters                          |
    +------------------------------------------------------------------+
    |        Key          |          Valid Values                      |
    | id                  | Integer: ID of product                     |
    | name                | String                                     |
    | classification      | ForeignKey: Classfication                  |
    | description         | String                                     |
    +------------------------------------------------------------------+

    Returns:     Array: Matching products are retuned in a list of hashes.

    Example:
    # Get all of product named 'Red Hat Enterprise Linux 5'
    >>> Product.filter({'name': 'Red Hat Enterprise Linux 5'})
    """
    return Product.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def filter_categories(request, query):
    """
    Description: Performs a search and returns the resulting list of categories.

    Params:      $query - Hash: keys must match valid search fields.

    +------------------------------------------------------------------+
    |              Component Search Parameters                         |
    +------------------------------------------------------------------+
    |        Key          |          Valid Values                      |
    | id                  | Integer: ID of product                     |
    | name                | String                                     |
    | product             | ForeignKey: Product                        |
    | description         | String                                     |
    +------------------------------------------------------------------+

    Returns:     Array: Matching categories are retuned in a list of hashes.

    Example:
    # Get all of categories named like 'libvirt'
    >>> Product.filter_categories({'name__icontains': 'regression'})
    # Get all of categories named in product 'Red Hat Enterprise Linux 5'
    >>> Product.filter_categories({'product__name': 'Red Hat Enterprise Linux 5'})
    """
    from tcms.testcases.models import TestCaseCategory

    return TestCaseCategory.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def filter_components(request, query):
    """
    Description: Performs a search and returns the resulting list of components.

    Params:      $query - Hash: keys must match valid search fields.

    +------------------------------------------------------------------+
    |              Component Search Parameters                         |
    +------------------------------------------------------------------+
    |        Key          |          Valid Values                      |
    | id                  | Integer: ID of product                     |
    | name                | String                                     |
    | product             | ForeignKey: Product                        |
    | initial_owner       | ForeignKey: Auth.User                      |
    | initial_qa_contact  | ForeignKey: Auth.User                      |
    | description         | String                                     |
    +------------------------------------------------------------------+

    Returns:     Array: Matching components are retuned in a list of hashes.

    Example:
    # Get all of components named like 'libvirt'
    >>> Product.filter_components({'name__icontains': 'libvirt'})
    # Get all of components named in product 'Red Hat Enterprise Linux 5'
    >>> Product.filter_components({'product__name': 'Red Hat Enterprise Linux 5'})
    """
    from tcms.management.models import Component

    return Component.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def filter_versions(request, query):
    """
    Description: Performs a search and returns the resulting list of versions.

    Params:      $query - Hash: keys must match valid search fields.

    +------------------------------------------------------------------+
    |              Component Search Parameters                         |
    +------------------------------------------------------------------+
    |        Key          |          Valid Values                      |
    | id                  | Integer: ID of product                     |
    | value               | String                                     |
    | product             | ForeignKey: Product                        |
    +------------------------------------------------------------------+

    Returns:     Array: Matching versions are retuned in a list of hashes.

    Example:
    # Get all of versions named like '2.4.0-SNAPSHOT'
    >>> Product.filter_versions({'value__icontains': '2.4.0-SNAPSHOT'})
    # Get all of filter_versions named in product 'Red Hat Enterprise Linux 5'
    >>> Product.filter_versions({'product__name': 'Red Hat Enterprise Linux 5'})
    """
    from tcms.management.models import Version

    return Version.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get(request, id):
    """
    Description: Used to load an existing product from the database.

    Params:      $id - An integer representing the ID in the database

    Returns:     A blessed TCMS Product object hash

    Example:
    >>> Product.get(61)
    """
    return Product.objects.get(id=int(id)).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def get_builds(request, product, is_active=True):
    """
    Description: Get the list of builds associated with this product.

    Params:      $product  -  Integer/String
                              Integer: product_id of the product in the Database
                              String: Product name
                 $is_active - Boolean: True to only include builds where is_active is true.
                              Default: True
    Returns:     Array: Returns an array of Build objects.

    Example:
    # Get with product id including all builds
    >>> Product.get_builds(61)
    # Get with product name excluding all inactive builds
    >>> Product.get_builds('Red Hat Enterprise Linux 5', 0)
    """
    from tcms.management.models import TestBuild

    p = pre_check_product(values=product)
    query = {'product': p, 'is_active': parse_bool_value(is_active)}
    return TestBuild.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_cases(request, product):
    """
    Description: Get the list of cases associated with this product.

    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Array: Returns an array of TestCase objects.

    Example:
    # Get with product id
    >>> Product.get_cases(61)
    # Get with product name
    >>> Product.get_cases('Red Hat Enterprise Linux 5')
    """
    from tcms.testcases.models import TestCase

    p = pre_check_product(values=product)
    query = {'category__product': p}
    return TestCase.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_categories(request, product):
    """
    Description: Get the list of categories associated with this product.

    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Array: Returns an array of Case Category objects.

    Example:
    # Get with product id
    >>> Product.get_categories(61)
    # Get with product name
    >>> Product.get_categories('Red Hat Enterprise Linux 5')
    """
    from tcms.testcases.models import TestCaseCategory

    p = pre_check_product(values=product)
    query = {'product': p}
    return TestCaseCategory.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_category(request, id):
    """
    Description: Get the category matching the given id.

    Params:      $id - Integer: ID of the category in the database.

    Returns:     Hash: Category object hash.

    Example:
    >>> Product.get_category(11)
    """
    from tcms.testcases.models import TestCaseCategory

    return TestCaseCategory.objects.get(id=int(id)).serialize()


@log_call(namespace=__xmlrpc_namespace__)
@permission_required('management.add_component', raise_exception=True)
def add_component(request, product, name, initial_owner_id=None, initial_qa_contact_id=None):
    """
    Description: Add component to selected product.


    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name
                 $name    - String: Component name
                 [$initial_owner_id] - Integer: (OPTIONAL) The numeric ID or the login
                                                           of the author.
                                    Defaults to logged in user.
                 [$initial_qa_contact_id] - Integer: (OPTIONAL) The numeric ID or the login
                                                                of the author.
                                         Defaults to logged in user.


    Returns:     Hash: Component object hash.

    Example:
    >>> Product.add_component(71, 'JPBMM')
    """
    from tcms.management.models import Component

    product = pre_check_product(values=product)

    if User.objects.filter(pk=initial_owner_id).exists():
        _initial_owner_id = initial_owner_id
    else:
        _initial_owner_id = request.user.pk

    if User.objects.filter(pk=initial_qa_contact_id).exists():
        _initial_qa_contact_id = initial_qa_contact_id
    else:
        _initial_qa_contact_id = request.user.pk

    return Component.objects.create(
        name=name,
        product=product,
        initial_owner_id=_initial_owner_id,
        initial_qa_contact_id=_initial_qa_contact_id,
    ).serialize()


@log_call(namespace=__xmlrpc_namespace__)
def get_component(request, id):
    """
    Description: Get the component matching the given id.

    Params:      $id - Integer: ID of the component in the database.

    Returns:     Hash: Component object hash.

    Example:
    >>> Product.get_component(11)
    """
    from tcms.management.models import Component

    return Component.objects.get(id=int(id)).serialize()


@log_call(namespace=__xmlrpc_namespace__)
@permission_required('management.change_component', raise_exception=True)
def update_component(request, component_id, values):
    """
    Description: Update component to selected product.

    Params:      $component_id - Integer: ID of the component in the database.

                 $values   - Hash of keys matching TestCase fields and the new values
                             to set each field to.

        +-----------------------+----------------+-----------------------------------------+
        | Field                 | Type           | Null                                    |
        +-----------------------+----------------+-----------------------------------------+
        | name                  | String         | Optional                                |
        | initial_owner_id      | Integer        | Optional(int - user_id)                 |
        | initial_qa_contact_id | Integer        | Optional(int - user_id)                 |
        +-----------------------+----------------+-----------------------------------------+

    Returns:     Hash: Component object hash.

    Example:
    >>> Product.update_component(71, {'name': 'NewName'})
    """
    from tcms.management.models import Component

    if not isinstance(values, dict) or 'name' not in values:
        raise ValueError('Component name is not in values {0}.'.format(values))

    name = values['name']
    if not isinstance(name, str) or len(name) == 0:
        raise ValueError('Component name {0} is not a string value.'.format(name))

    component = Component.objects.get(pk=int(component_id))
    component.name = name
    if values.get('initial_owner_id') and \
            User.objects.filter(pk=values['initial_owner_id']).exists():
        component.initial_owner_id = values['initial_owner_id']
    if values.get('initial_qa_contact_id') and \
            User.objects.filter(pk=values['initial_qa_contact_id']).exists():
        component.initial_qa_contact_id = values['initial_qa_contact_id']
    component.save()
    return component.serialize()


@log_call(namespace=__xmlrpc_namespace__)
def get_components(request, product):
    """
    Description: Get the list of components associated with this product.

    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Array: Returns an array of Component objects.

    Example:
    # Get with product id
    >>> Product.get_components(61)
    # Get with product name
    >>> Product.get_components('Red Hat Enterprise Linux 5')
    """
    from tcms.management.models import Component

    p = pre_check_product(values=product)
    query = {'product': p}
    return Component.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_environments(request, product):
    """FIXME: NOT IMPLEMENTED"""
    raise NotImplementedError('Not implemented RPC method')


@log_call(namespace=__xmlrpc_namespace__)
def get_milestones(request, product):
    """FIXME: NOT IMPLEMENTED"""
    raise NotImplementedError('Not implemented RPC method')


@log_call(namespace=__xmlrpc_namespace__)
def get_plans(request, product):
    """
    Description: Get the list of plans associated with this product.

    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Array: Returns an array of Test Plan objects.

    Example:
    # Get with product id
    >>> Product.get_plans(61)
    # Get with product name
    >>> Product.get_plans('Red Hat Enterprise Linux 5')
    """
    from tcms.testplans.models import TestPlan

    p = pre_check_product(values=product)
    query = {'product': p}
    return TestPlan.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_runs(request, product):
    """
    Description: Get the list of runs associated with this product.

    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Array: Returns an array of Test Run objects.

    Example:
    # Get with product id
    >>> Product.get_runs(61)
    # Get with product name
    >>> Product.get_runs('Red Hat Enterprise Linux 5')
    """
    from tcms.testruns.models import TestRun

    p = pre_check_product(values=product)
    query = {'build__product': p}
    return TestRun.to_xmlrpc(query)


@log_call(namespace=__xmlrpc_namespace__)
def get_tag(request, id):
    """
    Description: Get the list of tags.

    Params:      $id   - Integer: ID of the tag in the database.

    Returns:     Array: Returns an array of Tags objects.

    Example:
    >>> Product.get_tag(10)
    """
    from tcms.management.models import TestTag

    return TestTag.objects.get(pk=int(id)).serialize()


@log_call(namespace=__xmlrpc_namespace__)
@permission_required('management.add_version', raise_exception=True)
def add_version(request, values):
    """
    Description: Add version to specified product.

    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name
                 $value   - String
                            The name of the version string.

    Returns:     Array: Returns the newly added version object, error info if failed.

    Example:
    # Add version for specified product:
    >>> Product.add_version({'value': 'devel', 'product': 272})
    {'product': 'QE Test Product', 'id': '1106', 'value': 'devel', 'product_id': 272}
    # Run it again:
    >>> Product.add_version({'value': 'devel', 'product': 272})
    [['__all__', 'Version with this Product and Value already exists.']]
    """
    from tcms.management.forms import VersionForm
    from tcms.core import forms

    product = pre_check_product(values)
    form_values = values.copy()
    form_values['product'] = product.pk

    form = VersionForm(form_values)
    if form.is_valid():
        version = form.save()
        return version.serialize()
    else:
        raise ValueError(forms.errors_to_list(form))


@log_call(namespace=__xmlrpc_namespace__)
def get_versions(request, product):
    """
    Description: Get the list of versions associated with this product.

    Params:      $product - Integer/String
                            Integer: product_id of the product in the Database
                            String: Product name

    Returns:     Array: Returns an array of Version objects.

    Example:
    # Get with product id
    >>> Product.get_runs(61)
    # Get with product name
    >>> Product.get_runs('Red Hat Enterprise Linux 5')
    """
    from tcms.management.models import Version

    p = pre_check_product(values=product)
    query = {'product': p}
    return Version.to_xmlrpc(query)
