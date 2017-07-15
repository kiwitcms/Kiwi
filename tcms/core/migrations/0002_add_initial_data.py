# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forwards_add_initial_data(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.bulk_create([
        Group(name='Administrator'),
        Group(name='Tester'),
    ])

    Site = apps.get_model('sites', 'Site')
    Site.objects.create(name='localhost', domain='127.0.0.1:8000')


def reverse_remove_initial_data(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=['Administrator', 'Tester']).delete()

    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(name='localhost').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_django_comments__object_pk'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_add_initial_data, reverse_remove_initial_data)
    ]
