# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


test_case_statuss = ['PROPOSED', 'CONFIRMED', 'DISABLED', 'NEED_UPDATE']


def forwards_add_initial_data(apps, schema_editor):
    TestCaseBugSystem = apps.get_model('testcases', 'TestCaseBugSystem')
    TestCaseBugSystem.objects.bulk_create([
        TestCaseBugSystem(name='Bugzilla',
                          description='1-7 digit, e.g. 1001234',
                          url_reg_exp='https://bugzilla.example.com/show_bug.cgi?id=%s',
                          validate_reg_exp=r'^\d{1,7}$'),
        TestCaseBugSystem(name='JIRA',
                          description='e.g. KIWI-222',
                          url_reg_exp='https://jira.example.com/browse/%s',
                          validate_reg_exp=r'^[A-Z0-9]+-\d+$'),
    ])

    TestCaseStatus = apps.get_model('testcases', 'TestCaseStatus')
    TestCaseStatus.objects.bulk_create(
        [TestCaseStatus(name=name, description='') for name in test_case_statuss])


def reverse_add_initial_data(apps, schema_editor):
    TestCaseBugSystem = apps.get_model('testcases', 'TestCaseBugSystem')
    TestCaseBugSystem.objects.filter(name__in=['Bugzilla', 'JIRA']).delete()

    TestCaseStatus = apps.get_model('testcases', 'TestCaseStatus')
    TestCaseStatus.objects.filter(name__in=test_case_statuss).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0002_auto_20160828_1427'),
    ]

    operations = [
        migrations.RunPython(forwards_add_initial_data, reverse_add_initial_data)
    ]
