# Renames TCMSEnv* to Env*

from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('testruns', '0007_rename_testbuild_to_build'),
        ('management', '0007_rename_env'),
    ]

    operations = [
        migrations.RenameModel('TCMSEnvRunValueMap', 'EnvRunValueMap'),

        migrations.AlterField(
            model_name='EnvRunValueMap',
            name='value',
            field=models.ForeignKey(to='management.EnvValue', on_delete=models.CASCADE)),

        migrations.AlterField(
            model_name='TestRun',
            name='env_value',
            field=models.ManyToManyField(to='management.EnvValue',
                                         through='testruns.EnvRunValueMap')),

    ]
