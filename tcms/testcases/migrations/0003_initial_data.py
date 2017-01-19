# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def initial_data(apps, schema_editor):
    data = [
        {u'fields': {u'description': None, u'name': u'PROPOSED'},
         u'model': u'testcases.testcasestatus',
         u'pk': 1},
        {u'fields': {u'description': None, u'name': u'CONFIRMED'},
         u'model': u'testcases.testcasestatus',
         u'pk': 2},
        {u'fields': {u'description': None, u'name': u'DISABLED'},
         u'model': u'testcases.testcasestatus',
         u'pk': 3},
        {u'fields': {u'description': None, u'name': u'NEED_UPDATE'},
         u'model': u'testcases.testcasestatus',
         u'pk': 4},
        {u'fields': {u'description': u'',
                  u'name': u'Red Hat Bugzilla',
                  u'url_reg_exp': u'https://bugzilla.redhat.com/show_bug.cgi?id=%s'},
         u'model': u'testcases.testcasebugsystem',
         u'pk': 1},
        {u'fields': {u'description': u'JIRA',
                  u'name': u'JIRA',
                  u'url_reg_exp': u'https://projects.engineering.redhat.com/browse/%s'},
         u'model': u'testcases.testcasebugsystem',
         u'pk': 2}
    ]

    for record in data:
        app_name, model_name = record['model'].split('.')
        ModelClass = apps.get_model(app_name, model_name)
        R = ModelClass(**record['fields'])
        R.pk = record['pk']
        R.save()

class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0002_auto_20160323_1729')
    ]

    operations = [
        migrations.RunPython(initial_data),
    ]
