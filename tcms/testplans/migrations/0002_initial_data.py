# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def initial_data(apps, schema_editor):
    data = [
        {u'fields': {u'description': None, u'name': u'Unit'},
         u'model': u'testplans.testplantype',
         u'pk': 1},
        {u'fields': {u'description': None, u'name': u'Integration'},
         u'model': u'testplans.testplantype',
         u'pk': 2},
        {u'fields': {u'description': None, u'name': u'Function'},
         u'model': u'testplans.testplantype',
         u'pk': 3},
        {u'fields': {u'description': None, u'name': u'System'},
         u'model': u'testplans.testplantype',
         u'pk': 4},
        {u'fields': {u'description': None, u'name': u'Acceptance'},
         u'model': u'testplans.testplantype',
         u'pk': 5},
        {u'fields': {u'description': None, u'name': u'Installation'},
         u'model': u'testplans.testplantype',
         u'pk': 6},
        {u'fields': {u'description': None, u'name': u'Performance'},
         u'model': u'testplans.testplantype',
         u'pk': 7},
        {u'fields': {u'description': None, u'name': u'Product'},
         u'model': u'testplans.testplantype',
         u'pk': 8},
        {u'fields': {u'description': None, u'name': u'Interoperability'},
         u'model': u'testplans.testplantype',
         u'pk': 9},
        {u'fields': {u'description': u'Basic functionality', u'name': u'Smoke'},
         u'model': u'testplans.testplantype',
         u'pk': 10},
        {u'fields': {u'description': u'Known bugs/expliots', u'name': u'Regression'},
         u'model': u'testplans.testplantype',
         u'pk': 11}
    ]

    for record in data:
        app_name, model_name = record['model'].split('.')
        ModelClass = apps.get_model(app_name, model_name)
        R = ModelClass(**record['fields'])
        R.pk = record['pk']
        R.save()

class Migration(migrations.Migration):

    dependencies = [
        ('testplans', '0001_initial')
    ]

    operations = [
        migrations.RunPython(initial_data),
    ]
