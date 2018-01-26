# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method, REQUEST_KEY

from django.contrib.auth.models import User

from tcms.management.models import Product
from tcms.management.forms import VersionForm
from tcms.core.utils import form_errors_to_list
from tcms.xmlrpc.decorators import permissions_required
from tcms.xmlrpc.utils import pre_check_product, parse_bool_value


__all__ = (
    'check_component',
    'filter',
    'filter_components',
    'filter_versions',
    'get_builds',
    'get_cases',
    'add_component',
    'get_component',
    'update_component',
    'add_version',
)


@rpc_method(name='Product.check_component')
def check_component(name, product):
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


@rpc_method(name='Product.filter')
def filter(query):
    """
    Description: Performs a search and returns the resulting list of products.

    Params:      $query - Hash: keys must match valid search fields.

TODO: query keys match the product class

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


@rpc_method(name='Product.filter_components')
def filter_components(query):
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


@rpc_method(name='Product.filter_versions')
def filter_versions(query):
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


@rpc_method(name='Product.get_builds')
def get_builds(product, is_active=True):
    """
    Description: Get the list of builds associated with this product.
TODO: there's testbuilds.get for this ????

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


@rpc_method(name='Product.get_cases')
def get_cases(product):
    """
TODO: duplicate with api/testcases.py ???
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


@permissions_required('management.add_component')
@rpc_method(name='Product.add_component')
def add_component(product, name, **kwargs):
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

    initial_owner_id = kwargs.get('initial_owner_id', None)
    initial_qa_contact_id = kwargs.get('initial_qa_contact_id', None)
    request = kwargs.get(REQUEST_KEY)

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


@rpc_method(name='Product.get_component')
def get_component(id):
    """
    Description: Get the component matching the given id.

    Params:      $id - Integer: ID of the component in the database.

    Returns:     Hash: Component object hash.

    Example:
    >>> Product.get_component(11)
    """
    from tcms.management.models import Component

    return Component.objects.get(id=int(id)).serialize()


@permissions_required('management.change_component')
@rpc_method(name='Product.update_component')
def update_component(component_id, values):
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


@permissions_required('management.add_version')
@rpc_method(name='Product.add_version')
def add_version(values):
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

    product = pre_check_product(values)
    form_values = values.copy()
    form_values['product'] = product.pk

    form = VersionForm(form_values)
    if form.is_valid():
        version = form.save()
        return version.serialize()
    else:
        raise ValueError(form_errors_to_list(form))
