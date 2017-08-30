# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testcases', '0003_add_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcasebugsystem',
            name='name',
            field=models.CharField(unique=True, max_length=255),
        ),
    ]
