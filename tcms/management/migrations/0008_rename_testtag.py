# Renames TestTag to Tag

from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('management', '0007_rename_env'),
        # run after the migrations below b/c TestTag is referenced inside of them
        ('testcases', '0002_squashed'),
    ]

    operations = [
        migrations.RenameModel('TestTag', 'Tag'),
    ]
