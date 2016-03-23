# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tcms.core.models.base
from django.conf import settings
import tcms.core.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ('management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_pk', models.PositiveIntegerField(null=True, verbose_name=b'object ID', blank=True)),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254, db_index=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'tcms_contacts',
            },
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
                ('case_id', models.AutoField(max_length=10, serialize=False, primary_key=True)),
                ('create_date', models.DateTimeField(auto_now_add=True, db_column=b'creation_date')),
                ('is_automated', models.IntegerField(default=0, db_column=b'isautomated')),
                ('is_automated_proposed', models.BooleanField(default=False)),
                ('script', models.TextField(blank=True)),
                ('arguments', models.TextField(blank=True)),
                ('extra_link', models.CharField(default=None, max_length=1024, null=True, blank=True)),
                ('summary', models.CharField(max_length=255, blank=True)),
                ('requirement', models.CharField(max_length=255, blank=True)),
                ('alias', models.CharField(max_length=255, blank=True)),
                ('estimated_time', tcms.core.models.fields.DurationField(default=0, db_column=b'estimated_time')),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'test_cases',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestCaseAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'test_case_attachments',
            },
        ),
        migrations.CreateModel(
            name='TestCaseBug',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bug_id', models.CharField(max_length=25)),
                ('summary', models.CharField(max_length=255, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'db_table': 'test_case_bugs',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestCaseBugSystem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('url_reg_exp', models.CharField(max_length=8192)),
                ('validate_reg_exp', models.CharField(max_length=128)),
            ],
            options={
                'db_table': 'test_case_bug_systems',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestCaseCategory',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'category_id')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'test_case_categories',
                'verbose_name_plural': 'test case categories',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestCaseComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'test_case_components',
            },
        ),
        migrations.CreateModel(
            name='TestCaseEmailSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notify_on_case_update', models.BooleanField(default=False)),
                ('notify_on_case_delete', models.BooleanField(default=False)),
                ('auto_to_case_author', models.BooleanField(default=False)),
                ('auto_to_case_tester', models.BooleanField(default=False)),
                ('auto_to_run_manager', models.BooleanField(default=False)),
                ('auto_to_run_tester', models.BooleanField(default=False)),
                ('auto_to_case_run_assignee', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TestCasePlan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sortkey', models.IntegerField(null=True, blank=True)),
                ('case', models.ForeignKey(to='testcases.TestCase')),
            ],
            options={
                'db_table': 'test_case_plans',
            },
        ),
        migrations.CreateModel(
            name='TestCaseStatus',
            fields=[
                ('id', models.AutoField(max_length=6, serialize=False, primary_key=True, db_column=b'case_status_id')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'db_table': 'test_case_status',
                'verbose_name': 'Test case status',
                'verbose_name_plural': 'Test case status',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestCaseTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.IntegerField(default=b'0', db_column=b'userid')),
                ('case', models.ForeignKey(to='testcases.TestCase')),
                ('tag', models.ForeignKey(to='management.TestTag')),
            ],
            options={
                'db_table': 'test_case_tags',
            },
        ),
        migrations.CreateModel(
            name='TestCaseText',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('case_text_version', models.IntegerField()),
                ('create_date', models.DateTimeField(auto_now_add=True, db_column=b'creation_ts')),
                ('action', models.TextField(blank=True)),
                ('effect', models.TextField(blank=True)),
                ('setup', models.TextField(blank=True)),
                ('breakdown', models.TextField(blank=True)),
                ('action_checksum', models.CharField(max_length=32)),
                ('effect_checksum', models.CharField(max_length=32)),
                ('setup_checksum', models.CharField(max_length=32)),
                ('breakdown_checksum', models.CharField(max_length=32)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, db_column=b'who')),
                ('case', models.ForeignKey(related_name='text', to='testcases.TestCase')),
            ],
            options={
                'ordering': ['case', '-case_text_version'],
                'db_table': 'test_case_texts',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
    ]
