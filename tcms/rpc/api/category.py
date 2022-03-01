# -*- coding: utf-8 -*-

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.rpc.api.forms.testcase import CategoryForm
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import Category


@permissions_required("testcases.view_category")
@rpc_method(name="Category.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Category.filter(query)

        Search and return Category objects matching query.

        :param query: Field lookups for :class:`tcms.testcases.models.Category`
        :type query: dict
        :return: List of serialized :class:`tcms.testcases.models.Category` objects
        :rtype: list(dict)
    """
    return list(
        Category.objects.filter(**query)
        .values("id", "name", "product", "description")
        .distinct()
    )


@permissions_required("testcases.add_category")
@rpc_method(name="Category.create")
def create(values):
    """
    .. function:: RPC Category.create(values)

        Create a new Category object and store it in the database.

        :param values: Field values for :class:`tcms.testcases.models.Category`
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.Category` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *testcases.add_category* permission
    """
    form = CategoryForm(values)

    if form.is_valid():
        category = form.save()
        return model_to_dict(category)

    raise ValueError(form_errors_to_list(form))
