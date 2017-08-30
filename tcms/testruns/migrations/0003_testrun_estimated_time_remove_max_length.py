# -*- coding: utf-8 -*-
from django.db import migrations
import tcms.core.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0002_add_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testrun',
            name='estimated_time',
            field=tcms.core.models.fields.DurationField(default=0),
        ),
    ]
