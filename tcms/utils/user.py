# -*- coding: utf-8 -*-
from django.db import transaction


def delete_user(user):
    """
        Delete user across DB schemas.
    """
    if hasattr(user, 'tenant_set'):
        from django_tenants.utils import schema_context  # pylint: disable=import-error

        # using transactions b/c multiple schemas can refer to the same
        # user ID as FK references!
        with transaction.atomic():
            # delete user and all of its data across tenants
            for tenant in user.tenant_set.all():
                with schema_context(tenant.schema_name):
                    user.delete()

            # then delete everything from the public schema
            with schema_context('public'):
                user.delete()

    else:
        user.delete()
