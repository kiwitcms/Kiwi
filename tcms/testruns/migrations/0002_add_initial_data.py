# -*- coding: utf-8 -*-
from django.db import migrations


def forwards_add_initial_data(apps, schema_editor):
    TestCaseRunStatus = apps.get_model('testruns', 'TestCaseRunStatus')

    TestCaseRunStatus.objects.bulk_create([
        TestCaseRunStatus(name='IDLE', description='', sortkey=1),
        TestCaseRunStatus(name='RUNNING', description='', sortkey=2),
        TestCaseRunStatus(name='PAUSED', description='', sortkey=3),
        TestCaseRunStatus(name='PASSED', description='', sortkey=4),
        TestCaseRunStatus(name='FAILED', description='', sortkey=5),
        TestCaseRunStatus(name='BLOCKED', description='', sortkey=6),
        TestCaseRunStatus(name='ERROR', description='', sortkey=7),
        TestCaseRunStatus(name='WAIVED', description='', sortkey=8),
    ])


def reverse_add_initial_data(apps, schema_editor):
    TestCaseRunStatus = apps.get_model('testruns', 'TestCaseRunStatus')
    status_names = ['IDLE', 'RUNNING', 'PAUSED', 'PASSED', 'FAILED', 'BLOCKED', 'ERROR', 'WAIVED']
    TestCaseRunStatus.objects.filter(name__in=status_names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_add_initial_data, reverse_add_initial_data)
    ]
