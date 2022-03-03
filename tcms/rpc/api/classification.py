# Copyright (c) 2019-2021 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.core.utils import form_errors_to_list
from tcms.management.models import Classification
from tcms.rpc.api.forms.management import ClassificationForm
from tcms.rpc.decorators import permissions_required


@permissions_required("management.view_classification")
@rpc_method(name="Classification.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Classification.filter(query)

        Perform a search and return the resulting list of classifications.

        :param query: Field lookups for :class:`tcms.management.models.Classification`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Classification` objects
        :rtype: dict
    """
    return list(Classification.objects.filter(**query).values("id", "name").distinct())


@rpc_method(name="Classification.create")
@permissions_required("management.add_classification")
def create(values):
    """
    .. function:: RPC Classification.create(values)

        Create a new Classification object and store it in the database.

        :param values: Field values for :class:`tcms.management.models.Classification`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Classification` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *management.add_classification* permission
    """
    form = ClassificationForm(values)

    if form.is_valid():
        classification = form.save()
        return model_to_dict(classification)

    raise ValueError(form_errors_to_list(form))
