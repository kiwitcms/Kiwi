# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth.backends import ModelBackend

from tcms.utils.permissions import assign_default_group_permissions


class DBModelBackend(ModelBackend):
    can_login = True
    can_register = True
    can_logout = True


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
