# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import Group

from tcms.utils.permissions import assign_default_group_permissions


def initiate_user_with_default_setups(user):
    """
    Add default groups, permissions, status to a newly
    created user.
    """
    # create default permissions if not already set
    assign_default_group_permissions()

    default_groups = Group.objects.filter(name__in=settings.DEFAULT_GROUPS)
    for grp in default_groups:
        user.groups.add(grp)

    user.is_staff = True  # so they can add Products, Builds, etc via the ADMIN menu
    user.save()
