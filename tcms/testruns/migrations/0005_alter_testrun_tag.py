# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0004_remove_testrun_errata_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testruntag',
            name='run',
            field=models.ForeignKey(related_name='tags', to='testruns.TestRun'),
        ),
    ]
