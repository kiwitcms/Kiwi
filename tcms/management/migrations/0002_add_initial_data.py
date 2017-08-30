# -*- coding: utf-8 -*-
from django.db import migrations


def forwards_add_initial_data(apps, schema_editor):
    Priority = apps.get_model('management', 'Priority')
    Priority.objects.bulk_create([
        Priority(value='P1', sortkey=1),
        Priority(value='P2', sortkey=2),
        Priority(value='P3', sortkey=3),
        Priority(value='P4', sortkey=4),
        Priority(value='P5', sortkey=5),
    ])


def reverse_remove_initial_data(apps, schema_editor):
    Priority = apps.get_model('management', 'Priority')
    Priority.objects.filter(value__in=['P1', 'P2', 'P3', 'P4', 'P5']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_add_initial_data, reverse_remove_initial_data)
    ]
