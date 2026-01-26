# -*- coding: utf-8 -*-
from django.conf import settings
from django.forms.models import model_to_dict
from modernrpc.core import rpc_method

from tcms.management.models import Tag
from tcms.rpc.api.forms.management import TagForm
from tcms.rpc.decorators import permissions_required


@permissions_required("management.view_tag")
@rpc_method(name="Tag.filter")
def filter(query):  # pylint: disable=redefined-builtin
    """
    .. function:: RPC Tag.filter(query)

        Search and return a list of tags

        :param query: Field lookups for :class:`tcms.management.models.Tag`
        :type query: dict
        :return: Serialized list of :class:`tcms.management.models.Tag` objects
        :rtype: list(dict)
    """
    fields_list = ["id", "name", "case", "plan", "run"]
    if "tcms.bugs.apps.AppConfig" in settings.INSTALLED_APPS:
        fields_list.append("bugs")

    return list(
        Tag.objects.filter(**query).values(*fields_list).order_by("id").distinct()
    )


@permissions_required("management.add_tag")
@rpc_method(name="Tag.create")
def create(values):
    """
    .. function:: RPC Tag.create(values)

        Create a new Tag object and store it in the database.

        :param values: Field values for :class:`tcms.management.models.Tag`
        :type values: dict
        :return: Serialized :class:`tcms.management.models.Tag` object
        :rtype: dict
        :raises ValueError: if input values don't validate
        :raises PermissionDenied: if missing *management.add_tag* permission

    .. versionadded:: 15.2
    """
    form = TagForm(values)

    if form.is_valid():
        tag = form.save()
        return model_to_dict(tag)

    raise ValueError(list(form.errors.items()))
