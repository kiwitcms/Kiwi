# Renames TCMSEnv* to Env*

from django.db import migrations, models


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('management', '0006_rename_testbuild_to_build'),
    ]

    operations = [
        migrations.RenameModel('TCMSEnvGroup', 'EnvGroup'),
        migrations.RenameModel('TCMSEnvGroupPropertyMap', 'EnvGroupPropertyMap'),
        migrations.RenameModel('TCMSEnvProperty', 'EnvProperty'),
        migrations.RenameModel('TCMSEnvValue', 'EnvValue'),

        migrations.AlterField(
            model_name='EnvGroup',
            name='property',
            field=models.ManyToManyField(related_name='group',
                                         through='management.EnvGroupPropertyMap',
                                         to='management.EnvProperty')),

        migrations.AlterField(
            model_name='EnvGroupPropertyMap',
            name='group',
            field=models.ForeignKey(to='management.EnvGroup',
                                    on_delete=models.CASCADE)),

        migrations.AlterField(
            model_name='EnvGroupPropertyMap',
            name='property',
            field=models.ForeignKey(to='management.EnvProperty', on_delete=models.CASCADE)),

        migrations.AlterField(
            model_name='EnvValue',
            name='property',
            field=models.ForeignKey(related_name='value',
                                    to='management.EnvProperty',
                                    on_delete=models.CASCADE)),

    ]
