# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0005_change_meta_options_on_testcasebugsystem'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcasebugsystem',
            name='api_url',
            field=models.CharField(
                help_text=b'This is the URL to which API requests will be sent. Leave empty to disable!',
                max_length=1024,
                null=True,
                verbose_name=b'API URL',
                blank=True),
        ),
        migrations.AddField(
            model_name='testcasebugsystem',
            name='api_password',
            field=models.CharField(max_length=256, null=True, verbose_name=b'API password or token', blank=True),
        ),
        migrations.AddField(
            model_name='testcasebugsystem',
            name='api_username',
            field=models.CharField(max_length=256, null=True, verbose_name=b'API username', blank=True),
        ),
        migrations.AddField(
            model_name='testcasebugsystem',
            name='report_url',
            field=models.CharField(
                help_text=b'''For Bugzilla the report URL looks like
<strong>https://bugzilla.example.com/buglist.cgi?bugidtype=include&bug_id=1,2,3</strong>
<br/>so the value of this field must be <strong>https://bugzilla.example.com</strong>!
Leave empty to disable!''',
                max_length=1024, null=True, verbose_name=b'Report URL', blank=True),
        ),
        migrations.AddField(
            model_name='testcasebugsystem',
            name='tracker_type',
            field=models.CharField(
                default='IssueTrackerType',
                help_text=b'This determines how KiwiTestPad interfaces with the IT system',
                max_length=128,
                verbose_name=b'Type'),
        ),
    ]
