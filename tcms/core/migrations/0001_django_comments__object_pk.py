# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_comments', '__latest__'),
    ]

    operations = [
        migrations.AlterField('comment', 'object_pk', models.IntegerField())
    ]

    def __init__(self, name, app_label):
        super(Migration, self).__init__(name, app_label)
        self.app_label = 'django_comments'
