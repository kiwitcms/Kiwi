# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bookmark',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_pk', models.PositiveIntegerField(null=True, verbose_name=b'object ID', blank=True)),
                ('name', models.CharField(max_length=1024)),
                ('description', models.TextField(null=True, blank=True)),
                ('url', models.CharField(max_length=8192)),
            ],
            options={
                'db_table': 'tcms_bookmarks',
            },
        ),
        migrations.CreateModel(
            name='BookmarkCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tcms_bookmark_categories',
            },
        ),
        migrations.CreateModel(
            name='Groups',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('description', models.TextField()),
                ('isbuggroup', models.IntegerField()),
                ('userregexp', models.TextField()),
                ('isactive', models.IntegerField()),
            ],
            options={
                'db_table': 'groups',
            },
        ),
        migrations.CreateModel(
            name='Profiles',
            fields=[
                ('userid', models.AutoField(serialize=False, primary_key=True)),
                ('login_name', models.CharField(unique=True, max_length=255)),
                ('cryptpassword', models.CharField(max_length=128, blank=True)),
                ('realname', models.CharField(max_length=255)),
                ('disabledtext', models.TextField()),
                ('disable_mail', models.IntegerField(default=0)),
                ('mybugslink', models.IntegerField()),
                ('extern_id', models.IntegerField(blank=True)),
            ],
            options={
                'db_table': 'profiles',
            },
        ),
        migrations.CreateModel(
            name='UserGroupMap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('isbless', models.IntegerField(default=0)),
                ('grant_type', models.IntegerField(default=0)),
                ('group', models.ForeignKey(to='profiles.Groups')),
                ('user', models.OneToOneField(to='profiles.Profiles')),
            ],
            options={
                'db_table': 'user_group_map',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('phone_number', models.CharField(default=b'', max_length=128, blank=True)),
                ('url', models.URLField(default=b'', blank=True)),
                ('im', models.CharField(default=b'', max_length=128, blank=True)),
                ('im_type_id', models.IntegerField(default=1, null=True, blank=True)),
                ('address', models.TextField(default=b'', blank=True)),
                ('notes', models.TextField(default=b'', blank=True)),
                ('user', models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tcms_user_profiles',
            },
        ),
        migrations.AddField(
            model_name='bookmark',
            name='category',
            field=models.ForeignKey(related_name='bookmark', blank=True, to='profiles.BookmarkCategory', null=True),
        ),
        migrations.AddField(
            model_name='bookmark',
            name='content_type',
            field=models.ForeignKey(related_name='content_type_set_for_bookmark', verbose_name=b'content type', blank=True, to='contenttypes.ContentType', null=True),
        ),
        migrations.AddField(
            model_name='bookmark',
            name='site',
            field=models.ForeignKey(to='sites.Site'),
        ),
        migrations.AddField(
            model_name='bookmark',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterIndexTogether(
            name='bookmark',
            index_together=set([('content_type', 'object_pk', 'site')]),
        ),
    ]
