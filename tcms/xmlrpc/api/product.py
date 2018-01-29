# -*- coding: utf-8 -*-

from modernrpc.core import rpc_method

from tcms.management.models import Product
from tcms.xmlrpc.utils import pre_check_product


__all__ = (
    'filter',
    'get_cases',
)


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
