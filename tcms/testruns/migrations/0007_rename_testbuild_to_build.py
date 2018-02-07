# Renames Build to Build

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testruns', '0006_add_related_name_to_testrun'),
        ('management', '0006_rename_testbuild_to_build'),
    ]

    operations = [
        migrations.AlterField(
            model_name='TestCaseRun',
            name='build',
            field=models.ForeignKey(to='management.Build', on_delete=models.CASCADE)),

        migrations.AlterField(
            model_name='TestRun',
            name='build',
            field=models.ForeignKey(related_name='build_run', to='management.Build',
                                    on_delete=models.CASCADE)),
    ]
