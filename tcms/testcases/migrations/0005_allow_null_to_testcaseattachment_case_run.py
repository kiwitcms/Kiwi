# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0004_add_unique_to_testcasebugsystem_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcaseattachment',
            name='case_run',
            field=models.ForeignKey(related_name='case_run_attachment', default=None, blank=True, to='testruns.TestCaseRun', null=True, on_delete=models.CASCADE),
        ),
    ]
