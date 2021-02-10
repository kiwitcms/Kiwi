# -*- coding: utf-8 -*-
from django.conf import settings
from modernrpc.core import rpc_method

from tcms.management.models import Tag
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

    return list(Tag.objects.filter(**query).values(*fields_list).distinct())
