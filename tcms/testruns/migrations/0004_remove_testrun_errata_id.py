# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0003_testrun_estimated_time_remove_max_length'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testrun',
            name='errata_id',
        ),
    ]
