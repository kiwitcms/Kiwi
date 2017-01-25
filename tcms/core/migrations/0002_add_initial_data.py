# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards_add_initial_data(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.bulk_create([
        Group(name='Administrators'),
        Group(name='Testers'),
    ])

    Site = apps.get_model('sites', 'Site')
    Site.objects.create(name='Localhost', domain='nitrate.localhost')


def reverse_remove_initial_data(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Administrators', 'Testers']).delete()

    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(name='localhost').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_django_comments__object_pk'),
    ]

    operations = [
        migrations.RunPython(forwards_add_initial_data, reverse_remove_initial_data)
    ]
