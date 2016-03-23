# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tcms.core.models.base
from django.conf import settings
import tcms.core.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0001_initial'),
        ('management', '0001_initial'),
        ('testplans', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TCMSEnvRunValueMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'tcms_env_run_value_map',
            },
        ),
        migrations.CreateModel(
            name='TestCaseRun',
            fields=[
                ('case_run_id', models.AutoField(serialize=False, primary_key=True)),
                ('case_text_version', models.IntegerField()),
                ('running_date', models.DateTimeField(null=True, blank=True)),
                ('close_date', models.DateTimeField(null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
                ('sortkey', models.IntegerField(null=True, blank=True)),
                ('environment_id', models.IntegerField(default=0)),
                ('assignee', models.ForeignKey(related_name='case_run_assignee', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('build', models.ForeignKey(to='management.TestBuild')),
                ('case', models.ForeignKey(related_name='case_run', to='testcases.TestCase')),
            ],
            options={
                'db_table': 'test_case_runs',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestCaseRunStatus',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'case_run_status_id')),
                ('name', models.CharField(unique=True, max_length=60, blank=True)),
                ('sortkey', models.IntegerField(default=0, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('auto_blinddown', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'test_case_run_status',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestRun',
            fields=[
                ('run_id', models.AutoField(serialize=False, primary_key=True)),
                ('errata_id', models.IntegerField(null=True, blank=True)),
                ('plan_text_version', models.IntegerField()),
                ('start_date', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('stop_date', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('summary', models.TextField()),
                ('notes', models.TextField(blank=True)),
                ('estimated_time', tcms.core.models.fields.DurationField(default=0)),
                ('environment_id', models.IntegerField(default=0)),
                ('auto_update_run_status', models.BooleanField(default=False)),
                ('build', models.ForeignKey(related_name='build_run', to='management.TestBuild')),
            ],
            options={
                'db_table': 'test_runs',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestRunCC',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('run', models.OneToOneField(to='testruns.TestRun')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, db_column=b'who')),
            ],
            options={
                'db_table': 'test_run_cc',
            },
        ),
        migrations.CreateModel(
            name='TestRunTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.IntegerField(default=b'0', db_column=b'userid')),
                ('run', models.ForeignKey(to='testruns.TestRun')),
                ('tag', models.ForeignKey(to='management.TestTag')),
            ],
            options={
                'db_table': 'test_run_tags',
            },
        ),
        migrations.AddField(
            model_name='testrun',
            name='cc',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='testruns.TestRunCC'),
        ),
        migrations.AddField(
            model_name='testrun',
            name='default_tester',
            field=models.ForeignKey(related_name='default_tester', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='testrun',
            name='env_value',
            field=models.ManyToManyField(to='management.TCMSEnvValue', through='testruns.TCMSEnvRunValueMap'),
        ),
        migrations.AddField(
            model_name='testrun',
            name='manager',
            field=models.ForeignKey(related_name='manager', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='testrun',
            name='plan',
            field=models.ForeignKey(related_name='run', to='testplans.TestPlan'),
        ),
        migrations.AddField(
            model_name='testrun',
            name='product_version',
            field=models.ForeignKey(related_name='version_run', to='management.Version'),
        ),
        migrations.AddField(
            model_name='testrun',
            name='tag',
            field=models.ManyToManyField(to='management.TestTag', through='testruns.TestRunTag'),
        ),
        migrations.AddField(
            model_name='testcaserun',
            name='case_run_status',
            field=models.ForeignKey(to='testruns.TestCaseRunStatus'),
        ),
        migrations.AddField(
            model_name='testcaserun',
            name='run',
            field=models.ForeignKey(related_name='case_run', to='testruns.TestRun'),
        ),
        migrations.AddField(
            model_name='testcaserun',
            name='tested_by',
            field=models.ForeignKey(related_name='case_run_tester', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='tcmsenvrunvaluemap',
            name='run',
            field=models.ForeignKey(to='testruns.TestRun'),
        ),
        migrations.AddField(
            model_name='tcmsenvrunvaluemap',
            name='value',
            field=models.ForeignKey(to='management.TCMSEnvValue'),
        ),
        migrations.AlterUniqueTogether(
            name='testrun',
            unique_together=set([('run_id', 'product_version', 'plan_text_version')]),
        ),
        migrations.AlterUniqueTogether(
            name='testcaserun',
            unique_together=set([('case', 'run', 'case_text_version')]),
        ),
    ]
