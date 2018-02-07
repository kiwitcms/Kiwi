# Renames Build to Build

from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('management', '0005_remove_testenvironment_models'),
    ]

    operations = [
        migrations.RenameModel('TestBuild', 'Build')
    ]
