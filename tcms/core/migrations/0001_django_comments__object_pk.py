# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_comments', '0003_add_submit_date_index'),
    ]

    operations = [
        migrations.RunSQL('ALTER TABLE django_comments MODIFY object_pk INT NOT NULL;')
    ]
