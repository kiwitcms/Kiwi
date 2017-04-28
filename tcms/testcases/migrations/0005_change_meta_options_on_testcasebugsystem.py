# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0004_add_unique_to_testcasebugsystem_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='testcasebugsystem',
            options={'verbose_name': 'Bug tracker', 'verbose_name_plural': 'Bug trackers'},
        ),
        migrations.AlterField(
            model_name='testcasebugsystem',
            name='url_reg_exp',
            field=models.CharField(help_text=b'A valid Python format string such as http://bugs.example.com/%s', max_length=8192, verbose_name=b'URL format string'),
        ),
        migrations.AlterField(
            model_name='testcasebugsystem',
            name='validate_reg_exp',
            field=models.CharField(help_text=b'A valid JavaScript regular expression such as ^\\d$', max_length=128, verbose_name=b'RegExp for ID validation'),
        ),
    ]
