# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def initial_data(apps, schema_editor):
    data = [
        {u'fields': {u'is_active': True, u'sortkey': 100, u'value': u'P1'},
         u'pk': 1},
        {u'fields': {u'is_active': True, u'sortkey': 200, u'value': u'P2'},
         u'pk': 2},
        {u'fields': {u'is_active': True, u'sortkey': 300, u'value': u'P3'},
         u'pk': 3},
        {u'fields': {u'is_active': True, u'sortkey': 400, u'value': u'P4'},
         u'pk': 4},
        {u'fields': {u'is_active': True, u'sortkey': 500, u'value': u'P5'},
         u'pk': 5}
    ]

    Priority = apps.get_model("management", "Priority")
    for record in data:
        P = Priority(**record['fields'])
        P.pk = record['pk']
        P.save()

class Migration(migrations.Migration):

    dependencies = [
        ('management', '0002_auto_20160323_1729')
    ]

    operations = [
        migrations.RunPython(initial_data),
    ]
