# Copyright (c) 2025-2026 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 2.0: https://www.gnu.org/licenses/old-licenses/gpl-2.0.html

from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.rpc.api.forms.testcase import TemplateForm
from tcms.rpc.decorators import permissions_required
from tcms.testcases.models import Template


@permissions_required("testcases.view_template")
@rpc_method(name="Template.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Template.filter(query)

        Perform a search and return the resulting list of templates.

        :param query: Field lookups for :class:`tcms.testcases.models.Template`
        :type query: dict
        :return: Serialized list of :class:`tcms.testcases.models.Template` objects
        :rtype: dict
        :raises PermissionDenied: if missing *testcases.view_template* permission
    """
    return list(
        Template.objects.filter(**query)
        .values("id", "name", "text")
        .order_by("id")
        .distinct()
    )


@permissions_required("testcases.add_template")
@rpc_method(name="Template.create")
def create(values):
    """
    .. function:: RPC Template.create(values)

        Create a new Template object and store it in the database.

        :param values: Field values for :class:`tcms.testcases.models.Template`
        :type values: dict
        :return: Serialized :class:`tcms.testcases.models.Template` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *testcases.add_template* permission
    """
    form = TemplateForm(values)

    if form.is_valid():
        template = form.save()
        return model_to_dict(template)

    raise ValueError(list(form.errors.items()))
