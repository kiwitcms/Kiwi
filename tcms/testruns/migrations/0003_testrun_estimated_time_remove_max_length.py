# -*- coding: utf-8 -*-
from django.db import migrations


class Migration(migrations.Migration):
    """
        As part of migrating to Django's own DurationField
        we don't need this anymore.
    """
    dependencies = [
        ('testruns', '0002_add_initial_data'),
    ]

    # deliberately left empty
    operations = []
