# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards_add_default_perms(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')

    admin = Group.objects.get(name='Administrator')
    all_perms = Permission.objects.all()
    admin.permissions.add(*all_perms)

    tester = Group.objects.get(name='Tester')
    # apply all permissions for test case & product management
    for app_name in ['django_comments', 'management', 'testcases', 'testplans', 'testruns']:
        app_perms = Permission.objects.filter(content_type__app_label__contains=app_name)
        tester.permissions.add(*app_perms)


def reverse_remove_default_perms(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')

    admin = Group.objects.get(name='Administrator')
    admin.permissions.clear()

    tester = Group.objects.get(name='Tester')
    tester.permissions.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_initial_data'),
    ]

    operations = [
        migrations.RunPython(forwards_add_default_perms, reverse_remove_default_perms)
    ]
