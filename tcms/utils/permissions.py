# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group, Permission


def assign_default_group_permissions():
    """
        Adds the default permissions for Administrator and Tester
        groups!
    """
    admin = Group.objects.get(name='Administrator')
    if admin.permissions.count() == 0:
        all_perms = Permission.objects.all()
        admin.permissions.add(*all_perms)

    tester = Group.objects.get(name='Tester')
    if tester.permissions.count() == 0:
        # apply all permissions for test case & product management
        for app_name in ['django_comments', 'management', 'testcases', 'testplans', 'testruns']:
            app_perms = Permission.objects.filter(content_type__app_label__contains=app_name)
            tester.permissions.add(*app_perms)

    # this app was introduced later and we don't want all of its permissions
    if tester.permissions.filter(content_type__app_label='attachments').count() == 0:
        attachment_perms = Permission.objects.filter(
            content_type__app_label='attachments'
        ).exclude(codename='delete_foreign_attachments')
        tester.permissions.add(*attachment_perms)
