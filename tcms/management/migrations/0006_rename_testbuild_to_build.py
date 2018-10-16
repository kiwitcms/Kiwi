# Renames Build to Build

from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('management', '0001_squashed'),
    ]

    operations = [
        migrations.RenameModel('TestBuild', 'Build')
    ]
