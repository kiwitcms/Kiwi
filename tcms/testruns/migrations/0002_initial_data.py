# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def initial_data(apps, schema_editor):
    data = [
        {u'fields': {u'description': None, u'name': u'IDLE', u'sortkey': 1},
         u'pk': 1},
        {u'fields': {u'description': None, u'name': u'RUNNING', u'sortkey': 2},
         u'pk': 4},
        {u'fields': {u'description': None, u'name': u'PAUSED', u'sortkey': 3},
         u'pk': 5},
        {u'fields': {u'description': None, u'name': u'PASSED', u'sortkey': 4},
         u'pk': 2},
        {u'fields': {u'description': None, u'name': u'FAILED', u'sortkey': 5},
         u'pk': 3},
        {u'fields': {u'description': None, u'name': u'BLOCKED', u'sortkey': 6},
         u'pk': 6},
        {u'fields': {u'description': None, u'name': u'ERROR', u'sortkey': 7},
         u'pk': 7},
        {u'fields': {u'description': None, u'name': u'WAIVED', u'sortkey': 8},
         u'pk': 8}
    ]

    TestCaseRunStatus = apps.get_model("testruns", "TestCaseRunStatus")
    for record in data:
        S = TestCaseRunStatus(**record['fields'])
        S.pk = record['pk']
        S.save()

class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0001_initial')
    ]

    operations = [
        migrations.RunPython(initial_data),
    ]
