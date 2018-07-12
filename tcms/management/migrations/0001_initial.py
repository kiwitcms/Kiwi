# -*- coding: utf-8 -*-
from django.db import migrations, models
import tcms.core.models.base
from django.conf import settings


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
                ('initial_owner', models.ForeignKey(related_name='initialowner',
                                                    db_column='initialowner',
                                                    to=settings.AUTH_USER_MODEL, null=True,
                                                    on_delete=models.CASCADE)),
                ('initial_qa_contact', models.ForeignKey(related_name='initialqacontact',
                                                         db_column='initialqacontact', blank=True,
                                                         to=settings.AUTH_USER_MODEL, null=True,
                                                         on_delete=models.CASCADE)),
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
                ('is_active', models.BooleanField(default=True, db_column='isactive')),
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
                ('milestone_url', models.CharField(default='---', max_length=128,
                                                   db_column='milestoneurl')),
                ('disallow_new', models.BooleanField(default=False, db_column='disallownew')),
                ('vote_super_user', models.IntegerField(default=True, null=True,
                                                        db_column='votesperuser')),
                ('max_vote_super_bug', models.IntegerField(default=10000,
                                                           db_column='maxvotesperbug')),
                ('votes_to_confirm', models.BooleanField(default=False,
                                                         db_column='votestoconfirm')),
                ('default_milestone', models.CharField(default='---', max_length=20,
                                                       db_column='defaultmilestone')),
                ('classification', models.ForeignKey(to='management.Classification',
                                                     on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'products',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TCMSEnvGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('manager', models.ForeignKey(related_name='env_group_manager',
                                              to=settings.AUTH_USER_MODEL,
                                              on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='env_group_modifier', blank=True,
                                                  to=settings.AUTH_USER_MODEL, null=True,
                                                  on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'tcms_env_groups',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TCMSEnvGroupPropertyMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('group', models.ForeignKey(to='management.TCMSEnvGroup',
                                            on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'tcms_env_group_property_map',
            },
        ),
        migrations.CreateModel(
            name='TCMSEnvProperty',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
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
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('value', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('property', models.ForeignKey(related_name='value',
                                               to='management.TCMSEnvProperty',
                                               on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'tcms_env_values',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.CreateModel(
            name='TestAttachment',
            fields=[
                ('attachment_id', models.AutoField(max_length=10, serialize=False,
                                                   primary_key=True)),
                ('description', models.CharField(max_length=1024, null=True, blank=True)),
                ('file_name', models.CharField(unique=True, max_length=255, db_column='filename',
                                               blank=True)),
                ('stored_name', models.CharField(max_length=128, unique=True, null=True,
                                                 blank=True)),
                ('create_date', models.DateTimeField(db_column='creation_ts')),
                ('mime_type', models.CharField(max_length=100)),
                ('submitter', models.ForeignKey(related_name='attachments', blank=True,
                                                to=settings.AUTH_USER_MODEL, null=True,
                                                on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'test_attachments',
            },
        ),
        migrations.CreateModel(
            name='TestAttachmentData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                # formerly a custom BlobField
                ('contents', models.CharField(max_length=1, null=True, blank=True)),
                ('attachment', models.ForeignKey(to='management.TestAttachment',
                                                 on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'test_attachment_data',
            },
        ),
        migrations.CreateModel(
            name='TestBuild',
            fields=[
                ('build_id', models.AutoField(max_length=10, unique=True, serialize=False,
                                              primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('milestone', models.CharField(default='---', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True, db_column='isactive')),
                ('product', models.ForeignKey(related_name='build', to='management.Product',
                                              on_delete=models.CASCADE)),
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
                ('environment_id', models.AutoField(max_length=10, serialize=False,
                                                    primary_key=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('is_active', models.BooleanField(default=True, db_column='isactive')),
                ('product', models.ForeignKey(related_name='environments',
                                              to='management.Product',
                                              on_delete=models.CASCADE)),
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
                ('product', models.ForeignKey(related_name='environment_categories',
                                              to='management.Product', on_delete=models.CASCADE)),
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
                ('is_private', models.BooleanField(default=False, db_column='isprivate')),
                ('env_category', models.ForeignKey(to='management.TestEnvironmentCategory',
                                                   on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(related_name='parent_set',
                                             to='management.TestEnvironmentElement', null=True,
                                             on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'test_environment_element',
            },
        ),
        migrations.CreateModel(
            name='TestEnvironmentMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('value_selected', models.TextField(blank=True)),
                ('element', models.ForeignKey(to='management.TestEnvironmentElement',
                                              on_delete=models.CASCADE)),
                ('environment', models.ForeignKey(to='management.TestEnvironment',
                                                  on_delete=models.CASCADE)),
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
                ('valid_express', models.TextField(db_column='validexp', blank=True)),
                ('element', models.ForeignKey(to='management.TestEnvironmentElement',
                                              on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'test_environment_property',
            },
        ),
        migrations.CreateModel(
            name='TestTag',
            fields=[
                ('id', models.AutoField(max_length=10, serialize=False, primary_key=True,
                                        db_column='tag_id')),
                ('name', models.CharField(max_length=255, db_column='tag_name')),
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
                ('product', models.ForeignKey(related_name='version', to='management.Product',
                                              on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'versions',
            },
            bases=(models.Model, tcms.core.models.base.UrlMixin),
        ),
        migrations.AddField(
            model_name='testenvironmentmap',
            name='property',
            field=models.ForeignKey(to='management.TestEnvironmentProperty',
                                    on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='tcmsenvgrouppropertymap',
            name='property',
            field=models.ForeignKey(to='management.TCMSEnvProperty', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='tcmsenvgroup',
            name='property',
            field=models.ManyToManyField(related_name='group',
                                         through='management.TCMSEnvGroupPropertyMap',
                                         to='management.TCMSEnvProperty'),
        ),
        migrations.AddField(
            model_name='milestone',
            name='product',
            field=models.ForeignKey(to='management.Product', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='component',
            name='product',
            field=models.ForeignKey(related_name='component', to='management.Product',
                                    on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='version',
            unique_together=set([('product', 'value')]),
        ),
        migrations.AlterIndexTogether(
            name='testenvironmentcategory',
            index_together=set([('product', 'name'), ('env_category_id', 'product')]),
        ),
        migrations.AlterUniqueTogether(
            name='testbuild',
            unique_together=set([('product', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='tcmsenvvalue',
            unique_together=set([('property', 'value')]),
        ),
        migrations.AlterUniqueTogether(
            name='component',
            unique_together=set([('product', 'name')]),
        ),
    ]
