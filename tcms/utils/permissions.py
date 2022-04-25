# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import Group, Permission


def generate_output(output, permissions, group):
    """
    Generates verbose output for added permissions
    """
    if output:
        for perm in permissions:
            output.write(
                f"{perm.content_type.app_label}.{perm.codename} added to {group.name} group"
            )


def assign_default_group_permissions(
    output=None,
    refresh_all=False,
    group_model=Group,
    admin_permissions_filter=None,
    tester_permissions_filter=None,
):
    """
    Adds the default permissions for Administrator and Tester
    groups!
    """
    # arguments default to None due to security issues
    # with having an empty dict as the default value
    if admin_permissions_filter is None:
        admin_permissions_filter = {}

    if tester_permissions_filter is None:
        tester_permissions_filter = {}

    admin = group_model.objects.get(name="Administrator")
    if admin.permissions.count() == 0 or refresh_all:
        perms_to_add = Permission.objects.exclude(
            pk__in=admin.permissions.all()
        ).filter(**admin_permissions_filter)
        admin.permissions.add(*perms_to_add)
        generate_output(output, perms_to_add, admin)

    tester = group_model.objects.get(name="Tester")
    tester_perms = tester.permissions.all()
    if tester_perms.count() == 0 or refresh_all:
        # apply all permissions for test case & product management
        for app_name in [
            "attachments",
            "bugs",
            "django_comments",
            "linkreference",
            "management",
            "testcases",
            "testplans",
            "testruns",
        ]:
            app_perms = Permission.objects.filter(
                content_type__app_label=app_name
            ).filter(**tester_permissions_filter)
            app_perms = app_perms.exclude(pk__in=tester_perms).exclude(
                content_type__app_label="attachments",
                codename="delete_foreign_attachments",
            )
            tester.permissions.add(*app_perms)
            generate_output(output, app_perms, tester)


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
