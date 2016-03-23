# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tcms.core.models.base
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0001_initial'),
        ('management', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TestPlan',
            fields=[
                ('plan_id', models.AutoField(max_length=11, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('create_date', models.DateTimeField(auto_now_add=True, db_column=b'creation_date')),
                ('is_active', models.BooleanField(default=True, db_index=True, db_column=b'isactive')),
                ('extra_link', models.CharField(default=None, max_length=1024, null=True, blank=True)),
            ],
            options={
                'db_table': 'test_plans',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestPlanActivity',
            fields=[
                ('fieldid', models.IntegerField()),
                ('changed', models.DateTimeField(serialize=False, primary_key=True)),
                ('oldvalue', models.TextField(blank=True)),
                ('newvalue', models.TextField(blank=True)),
                ('plan', models.ForeignKey(to='testplans.TestPlan')),
                ('who', models.ForeignKey(to=settings.AUTH_USER_MODEL, db_column=b'who')),
            ],
            options={
                'db_table': 'test_plan_activity',
            },
        ),
        migrations.CreateModel(
            name='TestPlanAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.ForeignKey(to='management.TestAttachment')),
                ('plan', models.ForeignKey(to='testplans.TestPlan')),
            ],
            options={
                'db_table': 'test_plan_attachments',
            },
        ),
        migrations.CreateModel(
            name='TestPlanComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('component', models.ForeignKey(to='management.Component')),
                ('plan', models.ForeignKey(to='testplans.TestPlan')),
            ],
            options={
                'db_table': 'test_plan_components',
            },
        ),
        migrations.CreateModel(
            name='TestPlanEmailSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=False)),
                ('auto_to_plan_owner', models.BooleanField(default=False)),
                ('auto_to_plan_author', models.BooleanField(default=False)),
                ('auto_to_case_owner', models.BooleanField(default=False)),
                ('auto_to_case_default_tester', models.BooleanField(default=False)),
                ('notify_on_plan_update', models.BooleanField(default=False)),
                ('notify_on_plan_delete', models.BooleanField(default=False)),
                ('notify_on_case_update', models.BooleanField(default=False)),
                ('plan', models.OneToOneField(related_name='email_settings', to='testplans.TestPlan')),
            ],
        ),
        migrations.CreateModel(
            name='TestPlanPermission',
            fields=[
                ('userid', models.IntegerField(unique=True, serialize=False, primary_key=True)),
                ('permissions', models.IntegerField()),
                ('grant_type', models.IntegerField(unique=True)),
                ('plan', models.ForeignKey(to='testplans.TestPlan')),
            ],
            options={
                'db_table': 'test_plan_permissions',
            },
        ),
        migrations.CreateModel(
            name='TestPlanPermissionsRegexp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_regexp', models.TextField()),
                ('permissions', models.IntegerField()),
                ('plan', models.OneToOneField(to='testplans.TestPlan')),
            ],
            options={
                'db_table': 'test_plan_permissions_regexp',
            },
        ),
        migrations.CreateModel(
            name='TestPlanTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user', models.IntegerField(default=b'1', db_column=b'userid')),
                ('plan', models.ForeignKey(to='testplans.TestPlan')),
                ('tag', models.ForeignKey(to='management.TestTag')),
            ],
            options={
                'db_table': 'test_plan_tags',
            },
        ),
        migrations.CreateModel(
            name='TestPlanText',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('plan_text_version', models.IntegerField()),
                ('create_date', models.DateTimeField(auto_now_add=True, db_column=b'creation_ts')),
                ('plan_text', models.TextField(blank=True)),
                ('checksum', models.CharField(max_length=32)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, db_column=b'who')),
                ('plan', models.ForeignKey(related_name='text', to='testplans.TestPlan')),
            ],
            options={
                'ordering': ['plan', '-plan_text_version'],
                'db_table': 'test_plan_texts',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestPlanType',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, db_column=b'type_id')),
                ('name', models.CharField(unique=True, max_length=64)),
                ('description', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'test_plan_types',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.AddField(
            model_name='testplan',
            name='attachment',
            field=models.ManyToManyField(to='management.TestAttachment', through='testplans.TestPlanAttachment'),
        ),
        migrations.AddField(
            model_name='testplan',
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='testplan',
            name='case',
            field=models.ManyToManyField(to='testcases.TestCase', through='testcases.TestCasePlan'),
        ),
        migrations.AddField(
            model_name='testplan',
            name='component',
            field=models.ManyToManyField(to='management.Component', through='testplans.TestPlanComponent'),
        ),
        migrations.AddField(
            model_name='testplan',
            name='env_group',
            field=models.ManyToManyField(to='management.TCMSEnvGroup', through='management.TCMSEnvPlanMap'),
        ),
        migrations.AddField(
            model_name='testplan',
            name='owner',
            field=models.ForeignKey(related_name='myplans', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='testplan',
            name='parent',
            field=models.ForeignKey(related_name='child_set', blank=True, to='testplans.TestPlan', null=True),
        ),
        migrations.AddField(
            model_name='testplan',
            name='product',
            field=models.ForeignKey(related_name='plan', to='management.Product'),
        ),
        migrations.AddField(
            model_name='testplan',
            name='product_version',
            field=models.ForeignKey(related_name='plans', to='management.Version'),
        ),
        migrations.AddField(
            model_name='testplan',
            name='tag',
            field=models.ManyToManyField(to='management.TestTag', through='testplans.TestPlanTag'),
        ),
        migrations.AddField(
            model_name='testplan',
            name='type',
            field=models.ForeignKey(to='testplans.TestPlanType'),
        ),
        migrations.AlterUniqueTogether(
            name='testplantext',
            unique_together=set([('plan', 'plan_text_version')]),
        ),
        migrations.AlterUniqueTogether(
            name='testplanpermission',
            unique_together=set([('plan', 'userid')]),
        ),
        migrations.AlterUniqueTogether(
            name='testplancomponent',
            unique_together=set([('plan', 'component')]),
        ),
        migrations.AlterIndexTogether(
            name='testplan',
            index_together=set([('product', 'plan_id')]),
        ),
    ]
