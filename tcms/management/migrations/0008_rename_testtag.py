# Renames TestTag to Tag

from django.db import migrations


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('management', '0007_rename_env'),
        # run after the migrations below b/c TestTag is referenced inside of them
        ('testcases', '0012_alter_related_name_for_testcase'),
        ('testplans', '0007_add_related_name_to_testplan'),
        ('testruns', '0006_add_related_name_to_testrun'),
    ]

    operations = [
        migrations.RenameModel('TestTag', 'Tag'),
    ]
