# -*- coding: utf-8 -*-
from django.db import migrations


plan_types = [
    'Unit',
    'Integration',
    'Function',
    'System',
    'Acceptance',
    'Installation',
    'Performance',
    'Product',
    'Interoperability',
    'Smoke',
    'Regression',
]


def forwards_add_initial_data(apps, schema_editor):
    TestPlanType = apps.get_model('testplans', 'TestPlanType')

    TestPlanType.objects.bulk_create(
        [TestPlanType(name=name, description='') for name in plan_types])


def reverse_add_initial_data(apps, schema_editor):
    TestPlanType = apps.get_model('testplans', 'TestPlanType')
    TestPlanType.objects.filter(name__in=plan_types).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('testplans', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forwards_add_initial_data, reverse_add_initial_data)
    ]
