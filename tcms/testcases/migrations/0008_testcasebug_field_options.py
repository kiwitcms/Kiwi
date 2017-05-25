# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0007_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcasebugsystem',
            name='report_url',
            field=models.CharField(help_text=b'For Bugzilla the report URL looks like\n<strong>https://bugzilla.example.com/buglist.cgi?bugidtype=include&bug_id=1,2,3</strong>\n<br/>so the value of this field must be <strong>https://bugzilla.example.com</strong>!\nLeave empty to disable!\n', max_length=1024, null=True, verbose_name=b'Report URL', blank=True),
        ),
        migrations.AlterField(
            model_name='testcasebugsystem',
            name='tracker_type',
            field=models.CharField(default=b'IssueTrackerType', help_text=b'This determines how KiwiTestPad integrates with the IT system', max_length=128, verbose_name=b'Type'),
        ),
    ]
