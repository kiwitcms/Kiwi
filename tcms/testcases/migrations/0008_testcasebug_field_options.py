# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0007_merge'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcasebugsystem',
            name='report_url',
            field=models.CharField(help_text='For Bugzilla the report URL looks like\n'
                                             '<strong>https://bugzilla.example.com/'
                                             'buglist.cgi?bugidtype=include&bug_id=1,2,3'
                                             '</strong>\n<br/>so the value of this '
                                             'field must be <strong>'
                                             'https://bugzilla.example.com</strong>!\n'
                                             'Leave empty to disable!\n',
                                   max_length=1024, null=True, verbose_name='Report URL',
                                   blank=True),
        ),
        migrations.AlterField(
            model_name='testcasebugsystem',
            name='tracker_type',
            field=models.CharField(default='IssueTrackerType',
                                   help_text='This determines how Kiwi TCMS integrates '
                                             'with the IT system',
                                   max_length=128, verbose_name='Type'),
        ),
    ]
