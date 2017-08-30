# -*- coding: utf-8 -*-
from django.db import migrations


def delete_stale_content_type(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.filter(model='testplanpermission').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('testplans', '0002_add_initial_data'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='testplanpermission',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='testplanpermission',
            name='plan',
        ),
        migrations.DeleteModel(
            name='TestPlanPermission',
        ),
        migrations.RunPython(
            delete_stale_content_type
        ),
    ]
