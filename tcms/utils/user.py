# -*- coding: utf-8 -*-
from django.db import transaction

from tcms.signals import USER_DEACTIVATED_SIGNAL


def delete_user(user):
    """
    Delete user across DB schemas.
    """
    if hasattr(user, "tenant_set"):
        from django_tenants.utils import schema_context  # pylint: disable=E0401, C0415

        user_id = user.pk

        # using transactions b/c multiple schemas can refer to the same
        # user ID as FK references!
        with transaction.atomic():
            # delete user and all of its data across tenants
            for tenant in user.tenant_set.all():
                with schema_context(tenant.schema_name):
                    user.delete()
                    # reassign the ID b/c delete() sets it to None
                    user.pk = user_id

            # then delete everything from the public schema
            with schema_context("public"):
                user.delete()

    else:
        user.delete()


def deactivate(user):
    """
    Deactivates a user account!
    """

    # will not allow password reset if activated again
    user.set_password(None)
    user.is_active = False
    user.is_staff = False
    user.is_superuser = False
    user.save()

    # clear all individual permissions
    user.user_permissions.clear()

    # clear all group assignments
    user.groups.clear()

    USER_DEACTIVATED_SIGNAL.send(sender=None, user=user)
