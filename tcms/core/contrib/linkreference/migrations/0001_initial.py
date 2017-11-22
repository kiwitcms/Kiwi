# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LinkReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_pk', models.PositiveIntegerField(null=True, verbose_name='object ID', blank=True)),
                ('name', models.CharField(default='', max_length=64, blank=True)),
                ('url', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(related_name='content_type_set_for_linkreference', verbose_name='content type', blank=True, to='contenttypes.ContentType', null=True)),
                ('site', models.ForeignKey(to='sites.Site')),
            ],
            options={
                'db_table': 'tcms_linkrefs',
            },
        ),
        migrations.AlterIndexTogether(
            name='linkreference',
            index_together=set([('content_type', 'object_pk', 'site')]),
        ),
    ]
