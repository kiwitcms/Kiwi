# -*- coding: utf-8 -*-
from django.db import migrations, models


def forward_copy_data(apps, schema_editor):
    TestCaseBugSystem = apps.get_model('testcases', 'TestCaseBugSystem')
    for tc in TestCaseBugSystem.objects.all():
        tc.base_url = tc.report_url
        tc.save()


def reverse_copy_data(apps, schema_editor):
    TestCaseBugSystem = apps.get_model('testcases', 'TestCaseBugSystem')
    for tc in TestCaseBugSystem.objects.all():
        tc.report_url = tc.base_url
        tc.save()


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0008_testcasebug_field_options'),
    ]

    operations = [

        migrations.AddField(
            model_name='testcasebugsystem',
            name='base_url',
            field=models.CharField(help_text='Base URL, for example <strong>https://bugzilla.example.com</strong>!\nLeave empty to disable!\n', max_length=1024, null=True, verbose_name='Base URL', blank=True),
        ),
        migrations.RunPython(forward_copy_data, reverse_copy_data),
        migrations.RemoveField(
            model_name='testcasebugsystem',
            name='report_url',
        ),
    ]
