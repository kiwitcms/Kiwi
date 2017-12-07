# -*- coding: utf-8 -*-
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
            name='TCMSLogModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('object_pk', models.PositiveIntegerField(null=True, verbose_name='object ID',
                                                          blank=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('action', models.TextField()),
                ('content_type',
                 models.ForeignKey(related_name='content_type_set_for_tcmslogmodel',
                                   verbose_name='content type', blank=True,
                                   to='contenttypes.ContentType', null=True,
                                   on_delete=models.CASCADE)),
                ('site', models.ForeignKey(to='sites.Site', on_delete=models.CASCADE)),
                ('who', models.ForeignKey(related_name='log_who', to=settings.AUTH_USER_MODEL,
                                          on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
                'db_table': 'tcms_logs',
            },
        ),
        migrations.AlterIndexTogether(
            name='tcmslogmodel',
            index_together=set([('content_type', 'object_pk', 'site')]),
        ),
    ]
