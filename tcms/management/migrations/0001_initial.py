# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tcms.core.models.base
from django.conf import settings
import tcms.core.models.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Classification',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('description', models.TextField(blank=True)),
                ('sortkey', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'classifications',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.AutoField(max_length=5, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.TextField()),
            ],
            options={
                'db_table': 'components',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='Milestone',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('value', models.CharField(unique=True, max_length=60)),
                ('sortkey', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'milestones',
            },
        ),
        migrations.CreateModel(
            name='Priority',
            fields=[
                ('id', models.AutoField(max_length=5, serialize=False, primary_key=True)),
                ('value', models.CharField(unique=True, max_length=64)),
                ('sortkey', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True, db_column=b'isactive')),
            ],
            options={
                'db_table': 'priority',
                'verbose_name_plural': 'priorities',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(max_length=5, serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('description', models.TextField(blank=True)),
                ('milestone_url', models.CharField(default=b'---', max_length=128, db_column=b'milestoneurl')),
                ('disallow_new', models.BooleanField(default=False, db_column=b'disallownew')),
                ('vote_super_user', models.IntegerField(default=True, null=True, db_column=b'votesperuser')),
                ('max_vote_super_bug', models.IntegerField(default=10000, db_column=b'maxvotesperbug')),
                ('votes_to_confirm', models.BooleanField(default=False, db_column=b'votestoconfirm')),
                ('default_milestone', models.CharField(default=b'---', max_length=20, db_column=b'defaultmilestone')),
            ],
            options={
                'db_table': 'products',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TCMSEnvGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'tcms_env_groups',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TCMSEnvGroupPropertyMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'db_table': 'tcms_env_group_property_map',
            },
        ),
        migrations.CreateModel(
            name='TCMSEnvPlanMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group', models.ForeignKey(to='management.TCMSEnvGroup')),
            ],
            options={
                'db_table': 'tcms_env_plan_map',
            },
        ),
        migrations.CreateModel(
            name='TCMSEnvProperty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'tcms_env_properties',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TCMSEnvValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('property', models.ForeignKey(related_name='value', to='management.TCMSEnvProperty')),
            ],
            options={
                'db_table': 'tcms_env_values',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestAttachment',
            fields=[
                ('attachment_id', models.AutoField(max_length=10, serialize=False, primary_key=True)),
                ('description', models.CharField(max_length=1024, null=True, blank=True)),
                ('file_name', models.CharField(unique=True, max_length=255, db_column=b'filename', blank=True)),
                ('stored_name', models.CharField(max_length=128, unique=True, null=True, blank=True)),
                ('create_date', models.DateTimeField(db_column=b'creation_ts')),
                ('mime_type', models.CharField(max_length=100)),
                ('submitter', models.ForeignKey(related_name='attachments', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'test_attachments',
            },
        ),
        migrations.CreateModel(
            name='TestAttachmentData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('contents', tcms.core.models.fields.BlobField(blank=True)),
                ('attachment', models.OneToOneField(to='management.TestAttachment')),
            ],
            options={
                'db_table': 'test_attachment_data',
            },
        ),
        migrations.CreateModel(
            name='TestBuild',
            fields=[
                ('build_id', models.AutoField(max_length=10, unique=True, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('milestone', models.CharField(default=b'---', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True, db_column=b'isactive')),
                ('product', models.ForeignKey(related_name='build', to='management.Product')),
            ],
            options={
                'db_table': 'test_builds',
                'verbose_name': 'build',
                'verbose_name_plural': 'builds',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestEnvironment',
            fields=[
                ('environment_id', models.AutoField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('is_active', models.BooleanField(default=True, db_column=b'isactive')),
                ('product', models.ForeignKey(related_name='environments', to='management.Product')),
            ],
            options={
                'db_table': 'test_environments',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestEnvironmentCategory',
            fields=[
                ('env_category_id', models.AutoField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, blank=True)),
                ('product', models.ForeignKey(related_name='environment_categories', to='management.Product')),
            ],
            options={
                'db_table': 'test_environment_category',
            },
        ),
        migrations.CreateModel(
            name='TestEnvironmentElement',
            fields=[
                ('element_id', models.AutoField(max_length=10, serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, blank=True)),
                ('is_private', models.BooleanField(default=False, db_column=b'isprivate')),
                ('env_category', models.ForeignKey(to='management.TestEnvironmentCategory')),
                ('parent', models.ForeignKey(related_name='parent_set', to='management.TestEnvironmentElement', null=True)),
            ],
            options={
                'db_table': 'test_environment_element',
            },
        ),
        migrations.CreateModel(
            name='TestEnvironmentMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_selected', models.TextField(blank=True)),
                ('element', models.ForeignKey(to='management.TestEnvironmentElement')),
                ('environment', models.OneToOneField(to='management.TestEnvironment')),
            ],
            options={
                'db_table': 'test_environment_map',
            },
        ),
        migrations.CreateModel(
            name='TestEnvironmentProperty',
            fields=[
                ('property_id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, blank=True)),
                ('valid_express', models.TextField(db_column=b'validexp', blank=True)),
                ('element', models.ForeignKey(to='management.TestEnvironmentElement')),
            ],
            options={
                'db_table': 'test_environment_property',
            },
        ),
        migrations.CreateModel(
            name='TestTag',
            fields=[
                ('id', models.AutoField(max_length=10, serialize=False, primary_key=True, db_column=b'tag_id')),
                ('name', models.CharField(max_length=255, db_column=b'tag_name')),
            ],
            options={
                'db_table': 'test_tags',
                'verbose_name': 'tag',
                'verbose_name_plural': 'tags',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('value', models.CharField(max_length=192)),
                ('product', models.ForeignKey(related_name='version', to='management.Product')),
            ],
            options={
                'db_table': 'versions',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.AddField(
            model_name='testenvironmentmap',
            name='property',
            field=models.ForeignKey(to='management.TestEnvironmentProperty'),
        ),
    ]
